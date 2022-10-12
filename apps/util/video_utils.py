'''
Created on 12.10.2022

@author: jhirte
'''
import cv2
import numpy as np

def set_brightness(img, alpha=0):
    if alpha < 0:
        alpha += 1
        img_black = np.zeros([img.shape[0],img.shape[1],3],dtype=np.uint8)
        return cv2.addWeighted(img, alpha, img_black, 1 - alpha, 0)
    else:
        alpha = 1 - alpha
        img_white = np.full((img.shape[0],img.shape[1],3), 255, dtype=np.uint8)
        return cv2.addWeighted(img, alpha, img_white, 1 - alpha, 0)
    
