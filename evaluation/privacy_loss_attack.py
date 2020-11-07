#General Imports
import sys
import numpy as np
import pandas as pd
import argparse
import copy
import random
import json
import pickle

#PyTorch
import torch
from torch.autograd import grad
from torch import nn, optim
from torch.nn import functional as F
from torchvision import datasets, transforms
from torchvision.utils import save_image
from torch.autograd import Variable
import torch.utils.data as data_utils

#Tensorflow
from absl import flags
import tensorflow as tf
from tensorflow.keras import layers

#Sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from mia.estimators import ShadowModelBundle, AttackModelBundle, prepare_attack_data

from .base_eval import BaseEval
from utils.privacy_attack import to_onehot, mia



class PrivacyLossAttack(BaseEval):
    
    def __init__(self, args, train_dataset, val_dataset, test_dataset, base_res_dir, run, cuda):
        
        super().__init__(args, train_dataset, val_dataset, test_dataset, base_res_dir, run, cuda)
        
    
    def get_ce_loss(self):

        cross_entropy = torch.nn.CrossEntropyLoss(reduction='none')
        #Train Environment Data
        train_data={}
        train_data['loss']=[]
        train_data['labels']=[]
        for batch_idx, (x_e, y_e ,d_e, idx_e) in enumerate(self.train_dataset['data_loader']):
            #Random Shuffling along the batch axis
            rand_indices= torch.randperm(x_e.size()[0])
            x_e= x_e[rand_indices]
            y_e= y_e[rand_indices]
            
            with torch.no_grad():
                x_e= x_e.to(self.cuda)                
                y_e= y_e.to(self.cuda)
                
                out= self.forward(x_e)                
                loss=  cross_entropy(out, torch.argmax(y_e, dim=1).long()).to(self.cuda)
                train_data['loss'].append(loss)
                train_data['labels'].append(y_e)
        
        train_data['loss']= torch.cat(train_data['loss'], dim=0)
        train_data['labels']= torch.cat(train_data['labels'], dim=0)

        #Test Environment Data
        test_data={}
        test_data['loss']=[]
        test_data['labels']=[]
        for batch_idx, (x_e, y_e ,d_e, idx_e) in enumerate(self.test_dataset['data_loader']):
            #Random Shuffling along the batch axis
            rand_indices= torch.randperm(x_e.size()[0])
            x_e= x_e[rand_indices]
            y_e= y_e[rand_indices]

            with torch.no_grad():
                x_e= x_e.to(self.cuda)                
                y_e= y_e.to(self.cuda)
                
                out= self.forward(x_e)                
                loss=  cross_entropy(out, torch.argmax(y_e, dim=1).long()).to(self.cuda)
                
                test_data['loss'].append(loss)
                test_data['labels'].append(y_e)
        
        test_data['loss']= torch.cat(test_data['loss'], dim=0)
        test_data['labels']= torch.cat(test_data['labels'], dim=0)
        
        print('Train Logits: ', train_data['loss'].shape, 'Train Labels: ', train_data['labels'].shape )
        print('Test Logits: ', test_data['loss'].shape, 'Test Labels: ', test_data['labels'].shape )
    
        return train_data, test_data

    def create_attack_data(self, train_data, test_data, sample_size, case='train'):
        
        if case == 'train':
            train_loss= train_data['loss'][:sample_size]
            train_labels= train_data['labels'][:sample_size]

            test_loss= test_data['loss'][:sample_size]
            test_labels= test_data['labels'][:sample_size]
        elif case == 'test':
            train_loss= train_data['loss'][-1-sample_size:-1]
            train_labels= train_data['labels'][-1-sample_size:-1]

            test_loss= test_data['loss'][-1-sample_size:-1]
            test_labels= test_data['labels'][-1-sample_size:-1]            
        
        attack_data={}        
        attack_data['loss']= torch.cat( (train_loss, test_loss), dim=0 )
        attack_data['labels']= torch.cat( (train_labels, test_labels), dim=0 )
        attack_data['members']= torch.cat( (torch.ones((sample_size,1)), torch.zeros((sample_size,1))), dim=0).to(self.cuda)     
        print(case, attack_data['loss'].shape, attack_data['labels'].shape, attack_data['members'].shape)
        
        return attack_data
    
    def eval_entropy_attack(self, data, threshold_data, scale=1.0, case='train'):
        
        class_labels= torch.argmax(data['labels'], dim=1)
        acc=0.0
        size=0
        
        #Get class thresholds using only in members in train data
        if case == 'train':
            for y_c in range(self.args.out_classes):

                indices= class_labels == y_c
                loss= data['loss'][indices]
                labels= data['labels'][indices]
                members= data['members'][indices]
                members= members.view(members.shape[0])  
                
                indices= members == 1
                loss= loss[indices]
                labels= labels[indices]
                members= members[indices]

                metric= loss
                threshold_data[y_c]= torch.max(metric)
                print('Label: ', y_c, threshold_data[y_c])

                mem_predict= 1.0*(metric < threshold_data[y_c])
                acc= torch.sum( mem_predict == members ).item()
                size= mem_predict.shape[0]
                print('Accuracy: ', mem_predict[0], members[0], (mem_predict == members)[0], 100*acc/size )                
                
            return
            
        # Evaluate Membership Accuracy
        for y_c in range(self.args.out_classes):
            
            indices= class_labels == y_c
            loss= data['loss'][indices]
            labels= data['labels'][indices]
            members= data['members'][indices]
            members= members.view(members.shape[0])            
            
            metric= loss
            
            mem_predict= 1.0*(metric < (threshold_data[y_c]/scale))
            acc+= torch.sum( mem_predict == members ).item()
            size+= mem_predict.shape[0]
        
        print('Accuracy: ', case, 100*acc/size)
        return 100*acc/size
    
    def get_metric_eval(self):
        
        '''
          Train Size: 2*sample_size
          Test Size: 2*sample_size

        '''
        final_res={}
        acc_train=[]
        acc_test=[]
        precision=[]
        recall=[]
        
        sample_size= self.args.mia_sample_size
        
        # Create Attack Model train and test dataset
        train_data, test_data= self.get_ce_loss()
        train_attack_data= self.create_attack_data(train_data, test_data, sample_size, 'train')
        test_attack_data= self.create_attack_data(train_data, test_data, sample_size, 'test')
        
        threshold_data={}
        for y_c in range(self.args.out_classes):        
            threshold_data[y_c]=0
            
        self.eval_entropy_attack(train_attack_data, threshold_data, case='train')
        
        max_train_acc=0.0
        max_scale= -1
        lim_scale= max(threshold_data.values())
        if lim_scale <= 1:
            lim_scale = 10
        else:
            lim_scale =10*int(lim_scale)
         
        print('Upper Limit on Scale: ', lim_scale)
        for scale in np.random.randint(1, lim_scale, 10):
            train_metric= self.eval_entropy_attack(train_attack_data, threshold_data, scale= scale, case= 'test')
            print('Scale: ', scale, ' Acc: ', train_metric)
            if train_metric > max_train_acc:
                max_train_acc= train_metric
                max_scale= scale
            print('Max Scale: ', max_scale, 'Max Acc: ', max_train_acc)
             
        print('Threshold after training')
        for y_c in range(self.args.out_classes):
            print( 'Label : ', y_c, threshold_data[y_c]/max_scale )
        test_metric= self.eval_entropy_attack(test_attack_data, threshold_data, scale= max_scale, case= 'test')
        
        print('\nTrain Attack accuracy: ', max_train_acc)
        print('\nTest Attack accuracy: ', test_metric)

        self.metric_score['train_acc']= train_metric
        self.metric_score['test_acc']= test_metric

        return         