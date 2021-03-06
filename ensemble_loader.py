import torch
import torch.utils.data

import os

import numpy as np

import util.const as const
import util.load as load
import util.ensemble as ensemble
import util.submit as submit
import util.get_time as get_time
import util.exp as exp
import matplotlib.pyplot as plt

class EnsembleRunner(torch.utils.data.dataset.Dataset):
    def __init__(self, pred_dirs):
        self.pred_dirs = pred_dirs

        self.weights = ensemble.get_ensemble_weights(self.pred_dirs)

        first_pred_dir_path = os.path.join(const.OUTPUT_DIR, self.pred_dirs[0], const.PROBS_DIR_NAME)
        self.img_names = load.list_npy_in_dir(first_pred_dir_path)

        self.ensemble_dir = get_time.get_current_time()

        ensemble.create_models_ensembled(self.pred_dirs, self.ensemble_dir)
        return

    def __len__(self):
        return len(self.img_names)

    def __getitem__(self, idx):

        img_name = self.img_names[idx]
        ensembled = np.zeros(const.img_size)

        for i, pred_dir in enumerate(self.pred_dirs):
            pred_path = os.path.join(const.OUTPUT_DIR, pred_dir, const.PROBS_DIR_NAME, img_name + '.npy')
            img_prob = np.load(pred_path)

            weighted_img_prob = np.multiply(img_prob, self.weights[i])
            ensembled = np.add(ensembled, weighted_img_prob)

        # save into new output/ folder
        submit.save_ensembled_prob_map(self.ensemble_dir, img_name, ensembled)
        #plt.imshow(ensembled)
        #plt.show()

        return img_name, ensembled


def get_ensemble_loader(pred_dirs):

    dataset = EnsembleRunner(pred_dirs)

    loader = torch.utils.data.dataloader.DataLoader(
                                dataset,
                                batch_size=1,
                                shuffle=False,
                                num_workers=8,
                            )
    return loader
