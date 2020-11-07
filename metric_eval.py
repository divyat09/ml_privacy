import os
import sys

dataset=sys.argv[1]
metric=sys.argv[2]

if metric in ['acc', 'match_score', 'attribute_attack']:
    data_case= sys.argv[3]

train_domain_cases=['train_all']
test_domain_cases=['test_diff']

for test_case in test_domain_cases:
    for train_case in train_domain_cases:
        
        if metric == 'privacy_classifier':
            if dataset in ['rot_mnist', 'rot_mnist_spur']:
                base_script= 'python  test.py --test_metric mia --mia_logit 1 --mia_sample_size 2000 --batch_size 64 ' + ' --dataset ' + str(dataset)
            else:
                base_script= 'python  test.py --test_metric mia --mia_logit 1 --mia_sample_size 10000 --batch_size 64 ' + ' --dataset ' + str(dataset)

            res_dir= 'results/'+str(dataset)+'/privacy_classifier/'
            
        elif metric == 'privacy_entropy':
            if dataset in ['rot_mnist', 'rot_mnist_spur']:
                base_script= 'python  test.py --test_metric privacy_entropy --mia_sample_size 2000 --batch_size 64 ' + ' --dataset ' + str(dataset)
            elif dataset == 'fashion_mnist':
                base_script= 'python  test.py --test_metric privacy_entropy --mia_sample_size 10000 --batch_size 64 ' + ' --dataset ' + str(dataset)

            res_dir= 'results/'+str(dataset)+'/privacy_entropy/'
            
        elif metric == 'privacy_loss_attack':
            if dataset in ['rot_mnist', 'rot_mnist_spur']:
                base_script= 'python  test.py --test_metric privacy_loss_attack --mia_sample_size 2000 --batch_size 64 ' + ' --dataset ' + str(dataset)
            elif dataset == 'fashion_mnist':
                base_script= 'python  test.py --test_metric privacy_loss_attack --mia_sample_size 10000 --batch_size 64 ' + ' --dataset ' + str(dataset)
                
            res_dir= 'results/'+str(dataset)+'/privacy_loss/'
                
        elif metric == 'attribute_attack':
            base_script= 'python  test.py --test_metric attribute_attack --mia_logit 1 --batch_size 64 ' + ' --dataset ' + str(dataset) + ' --attribute_domain ' + data_case
                
            res_dir= 'results/'+str(dataset)+'/attribute_attack_' + data_case + '/'  
            
        elif metric == 'adv':
            base_script= 'python  test.py --test_metric adv_attack --adv_eps 0.3 ' + ' --dataset ' + str(dataset)
            res_dir= 'results/'+str(dataset)+'/adv/'
            
        elif metric  == 'acc':
            base_script= 'python test.py --test_metric acc ' + ' --dataset ' + str(dataset) + ' --acc_data_case ' + data_case
            res_dir= 'results/' + str(dataset) + '/acc_' + str(data_case) + '/'
            
        elif metric  == 'logit_hist':
            base_script= 'python test.py --test_metric logit_hist ' + ' --dataset ' + str(dataset)
            res_dir= 'results/' + str(dataset) + '/logit_hist/'
            
        elif metric  == 'match_score':
            base_script= 'python test.py --test_metric match_score ' + ' --dataset ' + str(dataset) + ' --match_func_data_case ' + data_case
            res_dir= 'results/' + str(dataset) + '/match_score_' + data_case + '/'
            
        #Train Domains 30, 45 case
        if train_case == 'train_abl':
            base_script+= ' --train_domains 30 45'
            res_dir= res_dir[:-1] +'_30_45/'
        
        #Test on 30, 45 angles instead of the standard 0, 90
        if test_case  == 'test_common':
            base_script += ' --test_domains 30 45'
            res_dir+= 'test_common_domains/'
            
        if not os.path.exists(res_dir):
            os.makedirs(res_dir)
        
        
        #Dataset Specific Modification
        if dataset == 'rot_mnist_spur':
            base_script+= ' --img_c 3 '
        
        #ERM
        case= res_dir + 'erm'
        script= base_script + ' --method_name erm_match --penalty_ws 0.0 --match_case 0.01 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'           
        os.system(script)
        
        #Random Match
        case= res_dir + 'random'     
        if dataset == 'rot_mnist_spur':        
            script= base_script + ' --method_name erm_match --penalty_ws 10.0 --match_case 0.01 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'   
        else:
            script= base_script + ' --method_name erm_match --penalty_ws 0.1 --match_case 0.01 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'   

        os.system(script)
        
        #Perfect Match
        case= res_dir + 'perfect'
        if dataset == 'rot_mnist_spur':                   
            script= base_script + ' --method_name erm_match --penalty_ws 10.0 --match_case 1.0 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'           
        else:
            script= base_script + ' --method_name erm_match --penalty_ws 0.1 --match_case 1.0 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'           
            
        os.system(script)
                
        #MatchDG
        case= res_dir + 'match_dg'
        if dataset == 'rot_mnist_spur':          
            script= base_script + ' --method_name matchdg_erm --penalty_ws 10.0 --match_case -1 --ctr_match_case 0.01 --ctr_match_flag 1 --ctr_match_interrupt 5 --n_runs 3 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'           
        else:
            script= base_script + ' --method_name matchdg_erm --penalty_ws 0.1 --match_case -1 --ctr_match_case 0.01 --ctr_match_flag 1 --ctr_match_interrupt 5 --n_runs 3 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'                       
        
        os.system(script)
        
        #CSD
        case= res_dir + 'csd'
        script= base_script + ' --method_name csd --penalty_ws 0.0 --match_case 0.01 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'
        os.system(script)
        
        #IRM
        case= res_dir + 'irm'
#         script= base_script + ' --method_name irm --penalty_ws 0.05 --penalty_s -1 --match_case 0.01 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'
        script= base_script + ' --method_name irm --match_case 0.01 ' + ' --logit_plot_path ' + case +  ' > ' + case + '.txt'
        os.system(script)        
        
