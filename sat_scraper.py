##CODE TO DOWNLOAD AND PROCESS IMAGES FROM THE MOSDAC WEBSITE##

from fileinput import filename
import time
import os, shutil
import argparse
import cv2
import numpy as np
import h5py
import glob
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

#global variables
slat=42.7       
slong= 53.0     
elat = -5.1     
elong = 102     
image_dim = 800 

parent_dir = os.path.dirname(os.path.abspath(__file__))
username = "kanak8278"
password = "jWdmAWJ8UT@QW2C"
start_date = '01-01-2022'
end_date = '01-02-2022'
num_files = 1 # number of files to be downloaded simultaneously

def create_direc():
    if not os.path.exists('tir1_channel_images'):
        os.makedirs('tir1_channel_images')
    if not os.path.exists('tir2_channel_images'):
        os.makedirs('tir2_channel_images')
    if not os.path.exists('wv_channel_images'):
        os.makedirs('wv_channel_images')

def compute_eye_r_c(lat, long):
    coord_r= int(abs(lat-slat)*image_dim/abs(elat-slat))
    coord_c= int(abs(long-slong)*image_dim/abs(elong-slong))
    return (coord_r,coord_c)

def process_image(image):
    norm_image= cv2.normalize(image,None,0,255, cv2.NORM_MINMAX,dtype=cv2.CV_32F)
    norm_image= cv2.resize(norm_image,(image_dim,image_dim))    
    cl_map= cv2.applyColorMap((norm_image).astype(np.uint8), cv2.COLORMAP_JET)    
    return cl_map

def get_patch(image, coord_r, coord_c):
    image_patch_size= 200
    image_patch = np.ones((2*image_patch_size, 2*image_patch_size , 3))

    for i in range(max(0,coord_r-image_patch_size),min(coord_r+image_patch_size, image.shape[0])):
        for j in range(max(0,coord_c-image_patch_size),min(coord_c+image_patch_size,image.shape[0])):
            for k in range(3):
                image_patch[i-coord_r+image_patch_size][j-coord_c+image_patch_size][k]= image[i][j][k]
            
    return image_patch


def write_channel_images(filepath):
    filename = filepath.split('.')[-2].split("\\")[-1]
    print("Processing file: " + filename+".h5 ...")
    data = h5py.File(filepath,'r')
    lat= 17.8     ##input variable
    long= 84.9    ## input variable
    
    coord_r,coord_c = compute_eye_r_c(lat,long)
    
    img_tir1= np.array(data['IMG_TIR1'])[0]
    img_tir2= np.array(data['IMG_TIR2'])[0]
    img_wv= np.array(data['IMG_WV'])[0]
    
    processed_img_tir1= process_image(img_tir1)
    processed_img_tir2= process_image(img_tir2)
    processed_img_wv= process_image(img_wv)
    
    tir1_patch = get_patch(processed_img_tir1, coord_r, coord_c)
    tir2_patch = get_patch(processed_img_tir2, coord_r, coord_c)
    wv_patch = get_patch(processed_img_wv, coord_r, coord_c)
    unique_path= filename+".jpg"
    cv2.imwrite(os.path.join("tir1_channel_images",unique_path), tir1_patch)
    cv2.imwrite(os.path.join("tir2_channel_images",unique_path), tir2_patch)
    cv2.imwrite(os.path.join("wv_channel_images",unique_path), wv_patch)


def download_and_process(request_id):
    browser = webdriver.Chrome('chromedriver.exe')
    browser.get('https://www.mosdac.gov.in/internal/uops')
    time.sleep(2)

    user = browser.find_element(By.ID, 'username')
    user.send_keys(username)
    passw = browser.find_element(By.ID, 'password')
    passw.send_keys(password)
    login = browser.find_element(By.ID, 'kc-login')
    login.click()

    time.sleep(2)
    status = browser.find_element(By.XPATH, '/html/body/div[6]/div[1]/ul/li[3]/a')
    status.click()
    archiv_req= browser.find_element(By.XPATH, '/html/body/div[6]/div[1]/ul/li[3]/ul/li[1]/a')
    archiv_req.click()

    time.sleep(2)
    download = browser.find_element(By.XPATH, '/html/body/div[7]/div/div[5]/div/table/tbody/tr[1]/td[7]/div[1]/a/img')
    download.click()

    time.sleep(2)
    browser.switch_to.window(browser.window_handles[1])
    order_= browser.find_element(By.XPATH, '/html/body/div/div/div/div/div/div[2]/div[2]/table/tbody/tr')
    order_.click()

    #loop from here
    time.sleep(2)
    order_table_path = "/html/body/div/div/div/div/div/div[2]/div[2]/table/tbody/tr"
    print("No of orders: ", len(browser.find_elements(By.XPATH, order_table_path))-1)
    folders = browser.find_elements(By.XPATH, order_table_path)

    for i in range(1,len(folders)):
        curr_f = folders[i]
        fold_name = curr_f.text.split('\n')[0]

        if(request_id== "all"):
            create_direc()
            print("Downloading all files folder wise...")
            print("Folder Name: ", fold_name)
            path = os.path.join(parent_dir, fold_name)
            if not os.path.exists(path):
                os.makedirs(path)
            download_path = path
            params = { 'behavior': 'allow', 'downloadPath': download_path }
            browser.execute_cdp_cmd('Page.setDownloadBehavior', params)
            time.sleep(2)
            curr_f.click()
            time.sleep(2)
            h5_files = browser.find_elements(By.XPATH, "/html/body/div/div/div/div/div/div[2]/div[2]/table/tbody/tr")
            print("No of files: ", len(h5_files))
            for j in range(2,len(h5_files),num_files):
                for j_ in range(j,j+num_files):
                    curr_h5 = h5_files[j_]
                    curr_h5.click()
                    print("Downloading file: ", curr_h5.text)
                    time.sleep(2)   
                wait_flag = True
                while wait_flag:
                    file_list_tmp = [fname.endswith('.h5') for fname in os.listdir(fold_name)]
                    if(sum(file_list_tmp)==num_files):
                        wait_flag = False
                    else:
                        time.sleep(2)
                file_list_final = [fname for fname in os.listdir(fold_name) if fname.endswith('.h5')]
                file_list_final = [os.path.join(fold_name, fname) for fname in file_list_final]
                for file_path in file_list_final:
                    write_channel_images(file_path)
                for filename in os.listdir(fold_name):
                    if filename.endswith(".h5"):
                        os.remove(os.path.join(fold_name, filename))                        
        elif(fold_name == request_id):
            create_direc()
            print("Downloading files for request id: ", request_id)
            path = os.path.join(parent_dir, fold_name)
            if not os.path.exists(path):
                os.makedirs(path)
            download_path = path
            params = { 'behavior': 'allow', 'downloadPath': download_path }
            browser.execute_cdp_cmd('Page.setDownloadBehavior', params)
            time.sleep(2)
            curr_f.click()
            time.sleep(2)
            h5_files = browser.find_elements(By.XPATH, "/html/body/div/div/div/div/div/div[2]/div[2]/table/tbody/tr")
            print("No of files: ", len(h5_files))
            for j in range(2,len(h5_files),num_files):
                for j_ in range(j,j+num_files):
                    curr_h5 = h5_files[j_]
                    curr_h5.click()
                    print("Downloading file: ", curr_h5.text)
                    time.sleep(2)   
                wait_flag = True
                while wait_flag:
                    file_list_tmp = [fname.endswith('.h5') for fname in os.listdir(fold_name)]
                    if(sum(file_list_tmp)==num_files):
                        wait_flag = False
                    else:
                        time.sleep(2)
                file_list_final = [fname for fname in os.listdir(fold_name) if fname.endswith('.h5')]
                file_list_final = [os.path.join(fold_name, fname) for fname in file_list_final]
                for file_path in file_list_final:
                    write_channel_images(file_path)
                for filename in os.listdir(fold_name):
                    if filename.endswith(".h5"):
                        os.remove(os.path.join(fold_name, filename)) 


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rid', type=str, default=None, help='Request Id')
    args = parser.parse_args()

    if args.rid is not None:
        download_and_process(args.rid)
