#Common imports
import os
import random
import copy
import numpy as np
import h5py
from PIL import Image

#Pytorch
import torch
import torch.utils.data as data_utils
from torchvision import datasets, transforms
from torchvision import datasets, transforms

#Base Class
from .data_loader import BaseDataLoader

class ChestXRayAugEval(BaseDataLoader):
    def __init__(self, args, list_train_domains, root, transform=None, data_case='train', match_func=False):
        
        super().__init__(args, list_train_domains, root, transform, data_case, match_func) 
        self.train_data, self.train_labels, self.train_domain, self.train_indices = self._get_data()

    def _get_data(self):
        
        data_dir= self.root
        to_pil = transforms.ToPILImage()
        to_tensor = transforms.ToTensor()
        
        # Choose subsets that should be included into the training
        training_list_img = {'aug':[], 'org':[] }
        training_list_labels = {'aug':[], 'org':[] }
        training_list_idx= {'aug':[], 'org':[] }
        training_list_size= {'aug':0, 'org':0 }
        training_out_classes={'aug':[], 'org':[] }
       
        image_counter=0
        for domain in self.list_train_domains:
            
            domain_imgs = torch.load(data_dir + domain + '_' + self.data_case + '_image.pt')
            domain_imgs_org = torch.load(data_dir + domain + '_' + self.data_case + '_image_org.pt')
            domain_labels = torch.load(data_dir + domain + '_' + self.data_case + '_label.pt')
            
            domain_idx= image_counter + np.array(list(range(len(domain_imgs))))
            domain_idx= domain_idx.tolist()
            image_counter+= len(domain_imgs)
            
            print('Image: ', domain_imgs.shape, ' Labels: ', domain_labels.shape)
            print('Source Domain ', domain)
            
            training_list_img['aug'].append(domain_imgs)
            training_list_img['org'].append(domain_imgs_org)
            
            training_list_labels['aug'].append(domain_labels)
            training_list_labels['org'].append(domain_labels)
            
            training_list_idx['aug'].append( domain_idx )            
            training_list_idx['org'].append( domain_idx )            
            
            training_list_size['aug']+= len(domain_imgs)
            training_list_size['org']+= len(domain_imgs)            
            
            training_out_classes['aug'].append( len(torch.unique(domain_labels))  )
            training_out_classes['org'].append( len(torch.unique(domain_labels))  )

                
        if self.match_func:
            print('Match Function Updates')
            num_classes= 2
            for y_c in range(num_classes):
                for key in ['aug', 'org']:
                    base_class_size=0
                    base_class_idx=-1                    
                    curr_class_size=0
                    for d_idx, domain in enumerate( self.list_train_domains ):
                        class_idx= training_list_labels[key][d_idx] == y_c
                        curr_class_size+= training_list_labels[key][d_idx][class_idx].shape[0]
                        
                    if base_class_size < curr_class_size:
                        base_class_size= curr_class_size
                        if key == 'aug':
                            base_class_idx= 0
                        else:
                            base_class_idx= 1                            
                    
                self.base_domain_size += base_class_size
                print('Max Class Size: ', base_class_size, base_class_idx, y_c )
        
                
        # Stack
        train_imgs = torch.cat(training_list_img['aug'] + training_list_img['org'] )
        train_labels = torch.cat(training_list_labels['aug'] + training_list_labels['org'] )
        train_indices = np.array(training_list_idx['aug']+training_list_idx['org']) 
        train_indices= np.hstack(train_indices)
        print('Train indices', len(np.unique(train_indices)) )
        training_out_classes= training_out_classes['aug'] + training_out_classes['org']
        self.training_list_size = [ training_list_size['aug'],  training_list_size['org'] ]           
        
        print(train_imgs.shape, train_labels.shape, train_indices.shape)
        print(self.training_list_size, self.base_domain_size)        
        print(training_out_classes)
        
        # Create domain labels
        train_domains = torch.zeros(train_labels.size())
        domain_start=0
        for idx in range(len(self.training_list_size)):
            curr_domain_size= self.training_list_size[idx]
            train_domains[ domain_start: domain_start+ curr_domain_size ] += idx
            domain_start+= curr_domain_size
            
        # Shuffle everything one more time
        inds = np.arange(train_labels.size()[0])
        np.random.shuffle(inds)
        train_imgs = train_imgs[inds]
        train_labels = train_labels[inds]
        train_domains = train_domains[inds].long()
        train_indices = train_indices[inds]

        # Convert to onehot
        out_classes= training_out_classes[0]
        y = torch.eye(out_classes)
        train_labels = y[train_labels]

        # Convert to onehot
        d = torch.eye(len(self.training_list_size))
        train_domains = d[train_domains]
        
        print(train_imgs.shape, train_labels.shape, train_domains.shape, train_indices.shape)
        # If shape (B,H,W) change it to (B,C,H,W) with C=1
        if len(train_imgs.shape)==3:
            train_imgs= train_imgs.unsqueeze(1)
        return train_imgs, train_labels, train_domains, train_indices