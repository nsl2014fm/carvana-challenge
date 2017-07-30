import torch
import numpy as np

import os
from datetime import datetime

import config
from model.unet import *

def create_if_not_exist(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

# Save predictions
def save_prediction(exp_name, epoch, img_name, pred_maps):

    pred_maps = pred_maps.astype(np.uint16)
    # TODO  does 0 to 65535 fit peak values in den maps?

    save_dir = os.path.join('./output', exp_name, str(epoch))
    create_if_not_exist(save_dir)

    filename = img_name + '.npy'
    save_path = os.path.join(save_dir, filename)

    np.save(save_path, pred_maps)
    print("Prediction density maps {} are saved. ".format(filename))
    return


def get_network(exp_name):
    model_name = exp_name.split('_')[0]

    if model_name == 'segnet':
        model = SimpleSegNet()
    elif model_name == 'unet':
        model = UNet()
    elif model_name == 'unet3l':
        model = UNet3l()
    elif model_name == 'unet2':
        model = UNet2()
    elif model_name == 'inceptionunet':
        model = InceptionUNet()
    elif model_name == 'inception2unet':
        model = Inception2UNet()
    elif model_name == 'denseunet':
        model = DenseUNet()
    elif model_name == 'dense':
        model = DenseNet()

    return model

def get_optimizer(model, exp_name):

    cfg = config.load_config_file(exp_name)

    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=cfg['learning_rate'],
        momentum=cfg['momentum'],
        weight_decay=cfg['weight_decay']
    )
    return optimizer


def save_checkpoint(exp_name, epoch, model_state_dict, optimizer_state_dict):

    state = {
        'exp_name': exp_name,
        'epoch': epoch,
        'state_dict': model_state_dict,
        'optimizer' : optimizer_state_dict,
    }

    filename = str(epoch) + '.pth.tar'
    save_path = os.path.join('./output', exp_name, filename)

    torch.save(state, save_path)
    return

def get_latest_ckpt(save_dir):
    ckpts = os.listdir(save_dir)
    ckpt_names = [ckpt.split('.')[0] for ckpt in ckpts if ckpt.endswith('.pth.tar')]

    if not ckpt_names:
        return '-1'

    print("All checkpoints:")
    print(ckpt_names)

    ckpt_epochs = [ int(ckpt_name) for ckpt_name in ckpt_names]

    latest_epoch = max(ckpt_epochs)
    latest_path = os.path.join(save_dir,  str(latest_epoch) + '.pth.tar')
    return latest_path

def load_exp(exp_name):
    save_dir = os.path.join('./output', exp_name)

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    ckpt_path = get_latest_ckpt(save_dir)
    model, optimizer, start_epoch = load_checkpoint(exp_name, ckpt_path)

    return model, optimizer, start_epoch

def load_checkpoint(exp_name, ckpt_path):
    if os.path.isfile(ckpt_path):
        print("=> loading checkpoint '{}'".format(ckpt_path))
        checkpoint = torch.load(ckpt_path)

        assert exp_name == checkpoint['exp_name']

        model = get_network(exp_name)
        model.load_state_dict(checkpoint['state_dict'])

        optimizer = get_optimizer(model, exp_name)
        optimizer.load_state_dict(checkpoint['optimizer'])

        start_epoch = checkpoint['epoch']

        print("=> loaded checkpoint '{}' (epoch {})"
              .format(ckpt_path, start_epoch))

    else:
        print("=> no checkpoint found at '{}'".format(ckpt_path))

        model = get_network(exp_name)
        optimizer = get_optimizer(model, exp_name)
        start_epoch = 1

    return model, optimizer, start_epoch


def setup_crayon(use_tensorboard, CrayonClient,exp_name):
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
