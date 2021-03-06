import torch

import os
from datetime import datetime

import util.const as const

import config
import model.unet as unet
import model.loss as loss


def create_dir_if_not_exist(dir):
    '''
    create directory if it doesn't exist
    '''
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def get_network(exp_name):
    '''
    get the first part in experiment name as model name
    '''
    model_name = exp_name.split('_')[0]

    model_type = getattr(unet, model_name)
    model = model_type()

    return model

def get_optimizer(model, exp_name):
    '''
    create oprimizer based on parameters loaded from config
    '''

    cfg = config.load_config_file(exp_name)

    optimizer_name = cfg['optimizer']

    optimizer_method = getattr(torch.optim, optimizer_name)
    optimizer = optimizer_method(
        model.parameters(),
        lr=cfg['learning_rate'],
        momentum=cfg['momentum'],
        weight_decay=cfg['weight_decay']
    )

    return optimizer


def get_criterion(exp_name):
    '''
    create loss function based on parameters loaded from config
    '''

    cfg = config.load_config_file(exp_name)

    criterion_name = cfg['criterion']
    loss_method = getattr(loss, criterion_name)
    criterion = loss_method()

    return criterion


def save_checkpoint(exp_name, epoch, model_state_dict, optimizer_state_dict):
    '''
    save the trained model as checkpoint
    '''

    state = {
        'exp_name': exp_name,
        'epoch': epoch,
        'state_dict': model_state_dict,
        'optimizer' : optimizer_state_dict,
    }

    filename = str(epoch) + '.pth.tar'
    save_path = os.path.join(const.OUTPUT_DIR, exp_name, filename)

    torch.save(state, save_path)
    return

def get_latest_ckpt(save_dir):
    '''
    find the .pth ckeckpoint file with latest epoch
    '''
    ckpts = os.listdir(save_dir)
    ckpt_names = [ckpt.split('.')[0] for ckpt in ckpts if ckpt.endswith('.pth.tar')]

    if not ckpt_names:
        print("No checkpoints found. It's a new experiment. ")
        return None

    print("All checkpoints:")
    print(ckpt_names)

    ckpt_epochs = [ int(ckpt_name) for ckpt_name in ckpt_names]

    latest_epoch = max(ckpt_epochs)
    latest_path = os.path.join(save_dir,  str(latest_epoch) + '.pth.tar')
    return latest_path

def load_exp(exp_name):
    '''
    load the latest previously saved model for this experiment
    '''
    save_dir = os.path.join(const.OUTPUT_DIR, exp_name)

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    ckpt_path = get_latest_ckpt(save_dir)
    model, optimizer, criterion, saved_epoch = load_checkpoint(exp_name, ckpt_path)
    start_epoch = saved_epoch + 1

    return model, optimizer, criterion, start_epoch

def load_checkpoint(exp_name, ckpt_path):
    '''
    load previously saved model
    '''
    if ckpt_path is not None and os.path.isfile(ckpt_path):
        print("=> loading checkpoint '{}'".format(ckpt_path))
        checkpoint = torch.load(ckpt_path)

        assert exp_name == checkpoint['exp_name']

        model = get_network(exp_name)
        model.load_state_dict(checkpoint['state_dict'])

        optimizer = get_optimizer(model, exp_name)
        optimizer.load_state_dict(checkpoint['optimizer'])

        saved_epoch = checkpoint['epoch']

        print("=> loaded checkpoint '{}' (epoch {})"
              .format(ckpt_path, saved_epoch))

    else:
        model = get_network(exp_name)
        optimizer = get_optimizer(model, exp_name)
        saved_epoch = 0

    criterion = get_criterion(exp_name)

    return model, optimizer, criterion, saved_epoch


def setup_crayon(use_tensorboard, CrayonClient,exp_name):
    '''
    create Crayon client
    '''
    # tensorboad
    experiment = None
    use_tensorboard = (use_tensorboard) and (CrayonClient is not None)
    if use_tensorboard and CrayonClient is not None:
        crayon_client = CrayonClient(hostname='127.0.0.1')
        # if remove_all_log:
        #     crayon_client.remove_all_experiments()

        timestamp  = datetime.now().strftime('_%d_%H-%M-%S')
        experiment = crayon_client.create_experiment(exp_name + timestamp)

    return experiment, use_tensorboard
