import torch
import scipy.misc as m
import os
import csv
import numpy as np
from tqdm import tqdm
from torch.utils import data
import cv2
from transforms import initAlignTransfer


class DataloaderAffectnet_MultiTask(data.Dataset):
    def __init__(self, img_size=128, exp_classes=7, is_transform=False):
        self.img_size = img_size
        self.is_transform = is_transform
        self.transform = initAlignTransfer(self.img_size, crop_size=self.img_size)
        self.exp_classes = exp_classes
        self.exp_lbl_list = []
        self.val_lbl_list, self.aro_lbl_list = [], []
        self.img_path_list = []

    # exp_csv_file(train/test): training_RAFModel.csv/validate.csv
    # va_csv_file(train/test): training.csv/validate.csv
    def load_data(self, exp_csv_file, va_csv_file, img_root):
        num = 0
        with open(exp_csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in tqdm(reader):
                num += 1
                cur_sample = {}
                cur_sample['img_path'] = os.path.join(img_root, row['subDirectory_filePath'].split('/')[1])
                # 0: Neutral, 1: Happy, 2: Sad, 3: Surprise, 4: Fear, 5: Disgust, 6: Anger, 7: Contempt
                # 8: None, 9: Uncertain, 10: No-Face
                cur_sample['expression'] = int(row['expression'][0:])
                cur_sample['valence'] = float(row['valence'])  # 0
                cur_sample['arousal'] = float(row['arousal'])  # 0
                if cur_sample['valence'] != -2 and 0 <= cur_sample['expression'] <= self.exp_classes-1:
                    self.img_path_list.append(cur_sample['img_path'])
                    self.exp_lbl_list.append(cur_sample['expression'])

        num=0
        with open(va_csv_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in tqdm(reader):
                num += 1
                cur_sample = {}
                cur_sample['img_path'] = os.path.join(img_root, row['subDirectory_filePath'].split('/')[1])
                cur_sample['expression'] = int(row['expression'][0:])
                cur_sample['valence'] = float(row['valence'])
                cur_sample['arousal'] = float(row['arousal'])
                if cur_sample['valence'] != -2 and 0 <= cur_sample['expression'] <= self.exp_classes-1:
                    self.val_lbl_list.append(cur_sample['valence'])
                    self.aro_lbl_list.append(cur_sample['arousal'])
        print('file preprocessing completed, find {} useful images'.format(len(self.img_path_list)))



    def __len__(self):
        return len(self.img_path_list)


    def __getitem__(self, index):
        img_path = self.img_path_list[index]
        img = cv2.imread(img_path, 1)  # BGR
        img = cv2.resize(img, (self.img_size, self.img_size))
        if self.is_transform:
            img = self.transform(img)

        img = img.transpose((2, 0, 1))  # [H,W,C] --> [C,H,W]
        img = ((img / 255.0 - 0.5) / 0.5)  # normalize to [-1, 1]

        img_path = self.img_path_list[index]
        exp_lbl = self.exp_lbl_list[index]
        val_lbl = self.val_lbl_list[index]
        aro_lbl = self.aro_lbl_list[index]
        va_lbl = np.array([val_lbl, aro_lbl])

        img = torch.from_numpy(img).float()
        va_lbl = torch.from_numpy(va_lbl).float()
        return img, exp_lbl, va_lbl, img_path
