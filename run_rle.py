import time
import argparse

import util.ensemble as ensemble
import util.submit as submit
import util.const as const

import rle_loader

def apply_rle(pred_dir, rle_loader):
    img_rles = {}

    for i, (img_name, rle) in enumerate(rle_loader):
        iter_start = time.time()
        assert len(img_name) == 1
        assert len(rle) == 1

        img_name = img_name[0]
        rle = rle[0]

        img_rles[img_name] = rle
        if (i % 1000) == 0:
            print('Iter {} / {}, time spent: {} sec'.format(i, len(rle_loader), time.time() - iter_start))

    # save into submission.csv
    submit.save_predictions(pred_dir, img_rles)
    return


if __name__ == "__main__":
    program_start = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument('pred_dir', nargs='?', default='0922-03:34:53')
    args = parser.parse_args()

    pred_dir = args.pred_dir

    exp_names, test_time_aug_names = ensemble.get_models_ensembled(pred_dir)
    print('The predictions are ensemble from {}. '.format(list(zip(exp_names, test_time_aug_names))))

    rle_loader = rle_loader.get_rle_loader(pred_dir)

    apply_rle(pred_dir, rle_loader)
    print('Total time spent: {} sec = {} hours'.format(time.time() - program_start, (time.time() - program_start) / 3600))
