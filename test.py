import torch
from torch.autograd import Variable

import time
import argparse

import util.exp as exp
import util.evaluation as evaluation
import util.visualization as viz
import util.submit as submit
import util.tile as tile
import util.crf as crf
import util.ensemble as ensemble
import util.augmentation as augmentation
import util.get_time as get_time

from dataloader import *
import config



def tester(exp_name, data_loader, tile_borders, net, criterion, is_val=False, test_time_aug_name=None, reverse_test_time_aug=None, paddings=None, is_ensemble=False, use_crf=False, DEBUG=False):
    if is_val:
        assert paddings is None  # When validating, paddings is not used
        assert not is_ensemble  # Never save predictions during validation
        assert test_time_aug_name is None  # No need to do Test Time augmententation when validating
    else:
        assert paddings is not None  # When testing, paddings is required
        assert test_time_aug_name is not None  # Test Time augmentation function is required when testing


    if torch.cuda.is_available():
        net.cuda()
        criterion = criterion.cuda()
    net.eval()  # Change model to 'eval' mode

    # initialize stats
    if is_val:
        epoch_val_loss = 0
        epoch_val_accuracy = 0
    else:
        print('Testing... ')
        tile_probs = {}

        if is_ensemble:
            print('Predictions will be saved for later post processing. ')
            print('Make sure you have at least 250 GB free disk space. ')
            img_rles = None
            ensemble_dir = get_time.get_current_time()
        else:
            print('Will generate submission.csv for submission. ')
            img_rles = {}

    epoch_start = time.time()

    for i, (img_name, images, targets) in enumerate(data_loader):
        iter_start = time.time()

        images = images.float()  # convert to FloatTensor
        targets = targets.float()

        images = Variable(images, volatile=True) # no need to compute gradients
        targets = Variable(targets, volatile=True)

        if torch.cuda.is_available():
            images = images.cuda()
            targets = targets.cuda()

        outputs = net(images)

        # remove tile borders
        images = tile.remove_tile_borders(images, tile_borders)
        outputs = tile.remove_tile_borders(outputs, tile_borders)

        if is_val:
            targets = tile.remove_tile_borders(targets, tile_borders)

        # compute dice
        masks = (outputs > 0.5).float()

        # apply CRF to image tiles
        if use_crf:
            masks = crf.run_crf(masks)

        iter_end = time.time()

        if is_val:
            accuracy = evaluation.dice_loss(masks, targets)
            loss = criterion(outputs, targets)

            # Update stats
            epoch_val_loss     += loss.data[0]
            epoch_val_accuracy += accuracy
        else:
            for img_idx in range(len(img_name)):
                tile_probs[img_name[img_idx]] = outputs.data[img_idx].cpu().numpy()

            # merge tile predictions into image predictions

            func_start = time.time()
            tile.merge_preds_if_possible(exp_name, tile_probs, paddings, img_rles, is_ensemble=is_ensemble, ensemble_dir=ensemble_dir, reverse_test_time_aug=reverse_test_time_aug)
            func_end = time.time()
            #print('merge_preds takes {:.2f} sec. '.format(func_end - func_start))

            iter_end = time.time()
            if (i % 2000) == 0:
                print('Iter {}/{}: {:.2f} sec spent'.format(i, len(data_loader), iter_end - iter_start))

        if DEBUG:
            # convert to numpy array
            image = images.data[0].cpu().numpy()
            mask = masks.data[0].cpu().numpy()
            target = targets.data[0].cpu().numpy()

            if is_val and accuracy < 0.98:
                print('Iter {}, {}: Loss {:.4f}, Accuracy: {:.5f}'.format(i, img_name, loss.data[0], accuracy))
                viz.visualize(image, mask, target)
            else:
                viz.visualize(image, mask)
    # for loop ends

    if is_val:
        epoch_val_loss     /= len(data_loader)
        epoch_val_accuracy /= len(data_loader)
        print('Validation Loss: {:.4f} Validation Accuracy:{:.5f}'.format(epoch_val_loss, epoch_val_accuracy))
    else:
        assert len(tile_probs) == 0  # all tile predictions should now be merged into image predictions now

        if is_ensemble:
            ensemble.mark_model_ensembled(ensemble_dir, exp_name, test_time_aug_name)
        else:
            submit.save_predictions(exp_name, img_rles)

    epoch_end = time.time()
    print('Total: {:.2f} sec = {:.1f} hour spent'.format(epoch_end - epoch_start, (epoch_end - epoch_start)/3600))

    if is_val:
        net.train()  # Change model bacl to 'train' mode
        return epoch_val_loss, epoch_val_accuracy
    else:
        return


if __name__ == "__main__":
    program_start = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument('exp_name', nargs='?', default='PeterUnet3_all_aug_1280')
    args = parser.parse_args()

    exp_name = args.exp_name

    cfg = config.load_config_file(exp_name)

    net, _, criterion, _ = exp.load_exp(exp_name)

    TTA_funcs = augmentation.get_TTA_funcs(cfg['test']['test_time_aug'])
    print('{} test time augmentations to be run...'.format(len(TTA_funcs)))

    for aug_name, test_time_aug, reverse_test_time_aug in TTA_funcs:
        print('\n\nNow running Test Tiem Augmentaion: {}'.format(aug_name))

        # data_loader, tile_borders = get_small_test_loader(
        data_loader, tile_borders = get_test_loader(
            cfg['test']['batch_size'],
            cfg['test']['paddings'],
            cfg['test']['tile_size'],
            test_time_aug,
        )

        tester(exp_name, data_loader, tile_borders, net, criterion, paddings=cfg['test']['paddings'], test_time_aug_name=aug_name, reverse_test_time_aug=reverse_test_time_aug, is_ensemble=True)
        # epoch_val_loss, epoch_val_accuracy = tester(exp_name, data_loader, tile_borders, net, criterion, is_val=True)

        # Note that CRF doesn't seem to improve results in previous experiments
    # for loop ends
    print('Total time spent: {} secs = {} hours'.format(time.time() - program_start, (time.time() - program_start)/3600))
