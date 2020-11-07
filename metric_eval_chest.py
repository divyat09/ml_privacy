import os
import sys

metric=sys.argv[1]

if metric == 'match_score':    
    base_script= 'python test.py --test_metric match_score --match_func_data_case test --match_func_aug_case 1 --dataset chestxray  --batch_size 64  --out_classes 2 --perfect_match 0 --img_c 3 --pre_trained 1 --model_name densenet121 --train_domains nih_trans chex_trans --test_domains kaggle'
    
    res_dir= 'results/chestxray/match_score/'
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)
        
elif metric == 'privacy_classifier':
    base_script= 'python test.py --test_metric mia --mia_sample_size 1000 --mia_logit 1 --dataset chestxray  --batch_size 64  --out_classes 2 --perfect_match 0 --img_c 3 --pre_trained 1 --model_name densenet121 --train_domains nih_trans chex_trans --test_domains kaggle'
    
    res_dir= 'results/chestxray/privacy_classifier/'
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)
    
elif metric == 'privacy_entropy':
    base_script= 'python test.py --test_metric privacy_entropy --mia_sample_size 1000 --dataset chestxray  --batch_size 64  --out_classes 2 --perfect_match 0 --img_c 3 --pre_trained 1 --model_name densenet121 --train_domains nih_trans chex_trans --test_domains kaggle'
    
    res_dir= 'results/chestxray/privacy_entropy/'
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

elif metric == 'privacy_loss_attack':
    base_script= 'python test.py --test_metric privacy_loss_attack --mia_sample_size 1000 --dataset chestxray  --batch_size 64  --out_classes 2 --perfect_match 0 --img_c 3 --pre_trained 1 --model_name densenet121 --train_domains nih_trans chex_trans --test_domains kaggle'
    
    res_dir= 'results/chestxray/privacy_loss/'
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)


elif metric == 'attribute_attack':
    base_script= 'python test.py --test_metric attribute_attack --mia_logit 1 --dataset chestxray  --batch_size 64  --out_classes 2 --perfect_match 0 --img_c 3 --pre_trained 1 --model_name densenet121 --train_domains nih_trans chex_trans --test_domains kaggle'
    
    res_dir= 'results/chestxray/attribute_attack/'
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

    
#ERM
script= base_script + ' --method_name erm_match --match_case 0.01 --penalty_ws 0 ' + ' > ' + res_dir + 'erm.txt'   
os.system(script)

#RandomMatch
script= base_script + ' --method_name erm_match --match_case 0.01 --penalty_ws 10.0 ' + ' > ' + res_dir + 'random.txt'   
os.system(script)

#MatchDG
script= base_script + '--method_name matchdg_erm --ctr_match_case 0.01 --ctr_match_flag 1 --ctr_match_interrupt 5 --ctr_model_name densenet121 --penalty_ws 50.0 --match_case -1 ' + ' > ' + res_dir + 'matchdg.txt'   
os.system(script)

#CSD
script= base_script + ' --method_name csd --match_case 0.01 --penalty_ws 0 ' + ' > ' + res_dir + 'csd.txt'   
os.system(script)

#IRM
script= base_script + ' --method_name irm --match_case 0.01 --penalty_s 5 --penalty_ws 10.0 ' + ' > ' + res_dir + 'irm.txt'   
os.system(script)