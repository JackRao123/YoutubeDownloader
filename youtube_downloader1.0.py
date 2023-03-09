import requests
import subprocess
import json
import os
import numpy as np
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

from moviepy.editor import *
from pytube import YouTube
import random
 
import cv2
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip #herere!

import time
from selenium import webdriver
 
from urllib.parse import urljoin

def get_video_length(filename):
    video = cv2.VideoCapture(filename)
    #duration = video.get(cv2.CAP_PROP_POS_MSEC) this doesn't work
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_rate = video.get(cv2.CAP_PROP_FPS)
    
    video_length = frame_count/frame_rate
    return video_length
 

def delete_videos(min_time, max_time, directory):#deletes any videos that are shorter than min_time, or longer than max_time, in folder directory.
    for filename in os.scandir(directory):
        filename = filename 
        file_path = filename.path

      

        duration = get_video_length(file_path)
        
        if(duration < min_time):
            os.remove(file_path)
        else:
            if(duration > max_time):
                os.remove(file_path)
                
        
                
def rename_videos(directory):
    count = 1 # !!!
    os.mkdir(directory + "NEW")
    for filename in os.scandir(directory):
        filename = filename 
        file_path = filename.path
        print(f"filename = {file_path}")
        new_name = directory + rf"NEW\VIDEO{count}.mp4" #the "NEW"  makes it so that it puts it in a new folder, because otherwise as names change it will rename files multiple times and fuck up the numbering.this also means we have to change 'directory' every time we run this, but we'll only have to run it once.
        #os.mkdir makes a new directory, places everything in ther.
        os.rename(file_path,new_name)#renames it, os.rename(oldname,newname)

        
        count = count + 1

def trimVid(input_name, start, end, output_name):
    #ffmpeg_extract_subclip(input_name,start,end,targetname = output_name)
    #ffmpeg  is sooooo much faster but makes random frames stutter
    clip = VideoFileClip(input_name).subclip(start,end)
    clip.write_videofile(output_name,
                          verbose=True,
                          codec="libx264",
                          audio_codec='aac',
                          temp_audiofile='temp-audio.m4a',
                          remove_temp=True, 
                          preset="medium",
                          ffmpeg_params=["-profile:v","baseline", "-level","3.0","-pix_fmt", "yuv420p"]) 
    #ffmpeg_extract_subclip(input_name, start, end, targetname=output_name)

 

def downloadYoutube(videourl, path): #downloads a single youtube video

    yt = YouTube(videourl)
    yt = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

    filesize = yt.filesize #filesize in bytes
    #if its greater than 25mb we wont download it.

    if filesize < 25000000:
        
        
        if not os.path.exists(path):
            os.makedirs(path)
        
        video_name = yt.title #this is the default name it will be saved as.

        

        
        print(f"ytl = {yt.filesize}")
        #Before we download we have to check if there's an existing file with the same (file lcoation). If there is, we have to name it something else as otherwise it will oevrwrite.
        desired_file_name = rf"{path}\{video_name}.mp4" #this is the filename it would be given by default
        file_exists = os.path.isfile(desired_file_name)

        index = 1
        while file_exists == True:
            desired_file_name = rf"{path}\{video_name} ({index}).mp4"
            file_exists = os.path.isfile(desired_file_name)
            index = index + 1 #do this to make sure if we download vids of duplicate file location, then instead of overwriting it just make another one with (1) or (2) at the end .

        try:   
            yt.download(path, filename = desired_file_name)
        except:
            try:
                yt.download(path, filename = rf"{path}\{random.randint(1,99999999)}.mp4")
            except:
                print("ERROR! ERROR! ERROR! ERROR! ERROR! ERROR! ERROR! ERROR! ERROR! ")
        print(f"Download completed: {videourl}...")
    else:
        print(f"Download for {videourl} cancelled, filesize too large.") 
    
def download_channel(channelURL, path): #downloads an entire youtube chanenl to folder path
    URL_array = get_channel_vids(channelURL)
    

    count = 1
    length = len(URL_array)
    for URL in URL_array:
        downloadYoutube(URL, path)
        print(f"{count} of {length} videos downloaded. \n")
        count = count + 1

def find_all(a_str, sub): #finds all index occurences of 'sub' in 'a_str'
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches
        
def get_channel_vids(URL): #gets urls of all youtube shorts of a channel url. returns list of urls
    ##### Web scrapper for infinite scrolling page #####
    driver = webdriver.Chrome(executable_path=r"E:\Chromedriver\chromedriver_win32_chrome83\chromedriver.exe")
    driver.get(URL)
    time.sleep(2)  # Allow 2 seconds for the web page to open
    scroll_pause_time = 0.4 # You can set your own pause time. My laptop is a bit slow so I use 1 sec
    screen_height = driver.execute_script("return window.screen.height;")   # get the screen height of the web



    i=0
    scroll_heights = []
    while True:
        driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))  
        # scroll one screen height each time
        i = i + 1
        time.sleep(scroll_pause_time)
        # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
        scroll_height = driver.execute_script("return document.documentElement.scrollHeight")  #basically represents how much we have scrolled
        scroll_heights.append(scroll_height)
        # Break the loop when the height when we reach the end(which is when the scroll_height stays constant)

        if(i>5): #
            if(scroll_heights[i-1] == scroll_heights[i-5-1]):#checks if the scrollheight has stopped changing (i.e. checks if we ve scrolled to the end
                break
            
         

        

    ##### the actual URLs #####
    urls = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for parent in soup.find_all(class_="style-scope ytd-rich-grid-slim-media"):
        a_tag = parent.find("a", class_="yt-simple-endpoint focus-on-expand style-scope ytd-rich-grid-slim-media")
         
     
        try:
            link = a_tag.attrs['href']

            fullURL = rf"https://www.youtube.com{link}"

            if(len(urls)>0):
                if(urls[-1] != fullURL):
                    urls.append(fullURL)
                    #print(fullURL)
            else:
                urls.append(fullURL)
        except Exception as e:
            #print(e)
            pass
                     
     
    print(f"urls = {urls}")
    return urls

def separateVideo(min_length, max_length, input_name, new_directory): #separates a long video into multiple small ones
    #new directory is necessary, it saves new ones in there so thta it doenst process clips multiple times.
    vid_length = get_video_length(input_name)

    lengths_array = [] #array of all the lengths of all the subclips.
    lengths_array = np.array(lengths_array)
    
    
    total_length = 0

    current_length = random.uniform(min_length,max_length)
    while total_length +current_length < vid_length: #separates big clip into small ones
        total_length = total_length + current_length
        lengths_array = np.append(lengths_array, current_length)
        current_length = random.uniform(min_length,max_length)
    
    remainder = vid_length - total_length

    print(f"len = {len(lengths_array)}")
    if(len(lengths_array)==0):
        print(vid_length)
        lengths_array = np.array([0])
        print(lengths_array)
    
        
  
        
        
    lengths_array = lengths_array + remainder/len(lengths_array) #leftover video, adds it back on.

    print(f"lengths array = {lengths_array}")
    #now, we make the clips
    
    #makeing sure for "new directory" that we make the new directory first.
    if os.path.exists(new_directory) == False:
        os.mkdir(new_directory)



    
    current_time = 0
    for i in range(len(lengths_array)):
        #we need to do some string processing, and then save it in a new folder.
        indexes_of_backslash = [x for x, char in enumerate(input_name) if char == '\\']
        desired_index_of_backslash = indexes_of_backslash[-1]
        actual_video_name = input_name[desired_index_of_backslash+1:]
        new_file_name = rf'{new_directory}\{actual_video_name[0:len(actual_video_name)- 4]}SUBCLIP{i+1}.mp4'
        print(f"newfilename = {new_file_name}")
        #rf'{input_name[0:len(input_name)- 4]}SUBCLIP{i}.mp4'
        
        trimVid(input_name, current_time, current_time + lengths_array[i-1], new_file_name)
        current_time = current_time + lengths_array[i-1]
 
    
    
    
    #clip = VideoFileClip(input_name).subclip

while True:
    a = input("link =")
    d = r'C:\Users\raoj6\Desktop\UNI\MATH1081'
    downloadYoutube(a,d)


  

#this version allows the file to be used from cmd.
if __name__ == '__main__':


    print(sys.argv)
    if len(sys.argv) > 1:
        function_name = sys.argv[1]

        #default_vid_directory = r'C:\Users\raoj6\Videos'
        

        

        match function_name:
            case 'dl':
                print("HI!")
                time.sleep(3)
                yt_link = sys.argv[2]
                if len(sys.argv > 3):
                        file_path = sys.argv[3]
                else:
                    file_path = default_vid_directory

                 
                if r'youtube.com/channel/' in yt_link or '@' in yt_link or 'youtube.com/c/' in yt_link:
                    #We are downloading a channel.
                    download_channel(yt_link, file_path)
                else:
                    #We are downloading a single video.
                    downloadYoutube(yt_link, file_path)

          




         
    else:
        print("Please specify a function name as an argument")










    
