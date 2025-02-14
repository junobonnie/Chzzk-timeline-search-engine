# -*- coding: utf-8 -*-
"""
Created on Tue Dec 24 12:00:27 2024

@author: replica
"""

import streamlit as st
import plotly.express as px
import requests
import time
from PIL import Image
from io import BytesIO
import numpy as np
import os.path

def peak_start(signal, height):
    start_index = []
    end_index = []
    is_start = False
    for i, s in enumerate(signal):
        if s > height and not is_start:
            start_index.append(i)
            is_start = True
        if s <= height and is_start:
            end_index.append(i)
            is_start = False
    return start_index, end_index
        
def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def is_include(white_list, content):
    for white_word in white_list:
        if white_word in content:
            return True
    return False

def second_to_strftime(second):
    return time.strftime('%H:%M:%S', time.gmtime(second))

def chat_download(video_no, duration):
    chat_url = "https://api.chzzk.naver.com/service/v1/videos/"+str(video_no)+"/chats"

    url = chat_url
    time_index = 0
    progress_text = "채팅 내역 다운로드 중. 길면 5분가량 소요."
    bar = st.progress(0, text=progress_text)
    
    with open("chat_log/"+str(video_no)+"_chat.txt", "w", encoding='utf-8') as f:
        while True:
            try:
                data = requests.get(url, headers=headers).json()
                next_time = data["content"]["nextPlayerMessageTime"]
                infos = data["content"]["videoChats"]
            except:
                time.sleep(30)
                data = requests.get(url, headers=headers).json()
                next_time = data["content"]["nextPlayerMessageTime"]
                infos = data["content"]["videoChats"]
            for info in infos:
                content = info["content"]
                tt = info["playerMessageTime"]//1000
                f.write(str(tt)+":"+content+"\n")
                bar.progress(tt/duration, text=progress_text)
            if next_time == None:
                bar.progress(1., text=progress_text)
                break
            url = chat_url + "?playerMessageTime="+str(next_time)     
    bar.empty()
    
def searching(video_no, duration, filter_):
    with open("chat_log/"+str(video_no)+"_chat.txt", "r", encoding='utf-8') as f:
        raw_data = f.readlines()
    
    t = [second_to_strftime(i) for i in range(duration+60)]
    kk = np.zeros(duration+60)

    for raw in raw_data:
        
        #print(raw)
        try:
            tt, content = raw.split(":", 1)
        except:
            content = ""
        #filter_ = ["{:d_47:}", "{:d_48:}", "{:d_60:}"]
        #filter_ = ["귀엽", "귀여", "ㄱㅇㅇ"]
        #filter_ = ["마스터얍", "마스터 얍"]
        if is_include(filter_, content):
            kk[int(tt)] += 1
    return t, kk
    
def plotting(video_no, duration):
    with open("config", "r") as f:
        config = f.readlines()
        time.sleep(0.5)
        
    with open("filter.txt", "r") as ff:
        filter__ = ff.readlines()
        time.sleep(0.5)
    
    
    threshold = st.slider('Threshold', 0., 1., float(config[0]))
    smoothing_level = st.slider('Smoothing Level', 1, 200, int(config[1]))
    filter_ = st.text_area('검색 필터 입력(줄넘김으로 구분)', value="".join(filter__)).split("\n")
    st.write("필터값", filter_)
    
    
    if st.button('검색'):
        with open("config", "w") as f:
            f.write(str(threshold)+"\n")
            f.write(str(smoothing_level))
        with open("filter.txt", "w") as f:
            f.write("\n".join(filter_))
        t, kk = searching(video_no, duration, filter_)
        smooth_kk = smooth(kk, smoothing_level)
        start_index, end_index = peak_start(smooth_kk, threshold)
        fig = px.line(x=t, y=smooth_kk, title='차트').update_layout(xaxis_title="time", yaxis_title="chat/s")
        fig.add_hline(y=threshold, line_color="red")
        # Plot!
        st.plotly_chart(fig, use_container_width=True)
       
        ep = st.expander('타임 테이블')
        for i, s in enumerate(start_index):
            try:
                ep.write(second_to_strftime(s)+" ~ "+second_to_strftime(end_index[i]))
            except:
                ep.write(second_to_strftime(s)+" ~ "+second_to_strftime(duration))


def review_list_data(review_list_url):
    content = requests.get(review_list_url, headers=headers).json()["content"]
    review_infos = content["data"]
    total_pages = content["totalPages"]
    for i, review_info in enumerate(review_infos):
        image_url = review_info["thumbnailImageUrl"]
        if image_url is None:
            review_info["image"] = Image.open("adult.png")
        else:
            response = requests.get(image_url)
            review_info["image"] = Image.open(BytesIO(response.content))
    return review_infos, total_pages

@st.dialog("채팅내역 검색하기", width="large")
def chat_searching(video_no, duration):
    url = "https://chzzk.naver.com/video/"+str(video_no)
    st.markdown("[다시보기 링크](%s)" %("https://chzzk.naver.com/video/"+str(video_no)))
    if os.path.exists("chat_log/"+str(video_no)+"_chat.txt"):
        pass
    else:
        chat_download(video_no, duration)
    plotting(video_no, duration)

###############################################################################

headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
col_num = 3

st.set_page_config(layout="wide")
st.text_input("스트리머 방송주소 넣기", key = "stream_url")
st.write(st.session_state.stream_url)
streamer_no = st.session_state.stream_url.split("/")[-1]

if "page" not in st.session_state:
    st.session_state.page = 0
    st.session_state.old_page = 0
    
if "streamer_no" in st.session_state:
    cols = st.columns(col_num)
    ct = [cols[i].container() for i in range(col_num)]
    
    if (not "review_infos" in st.session_state) or (st.session_state.streamer_no != streamer_no):
        st.session_state.page = 0
        st.session_state.old_page = 0
        review_list_url = "https://api.chzzk.naver.com/service/v1/channels/"+streamer_no+"/videos?sortType=LATEST&pagingType=PAGE&page="+str(st.session_state.page)+"&size=50&publishDateAt=&videoType="

        with st.spinner(text="다시보기 정보 다운로드 중"):
            st.session_state.review_infos, st.session_state.total_pages = review_list_data(review_list_url)
            
    elif st.session_state.page != st.session_state.old_page:
        review_list_url = "https://api.chzzk.naver.com/service/v1/channels/"+streamer_no+"/videos?sortType=LATEST&pagingType=PAGE&page="+str(st.session_state.page)+"&size=50&publishDateAt=&videoType="

        with st.spinner(text="다시보기 정보 다운로드 중"):
            st.session_state.review_infos, st.session_state.total_pages = review_list_data(review_list_url)
        
    for i, review_info in enumerate(st.session_state.review_infos):
        title = review_info["videoTitle"]
        date = review_info["publishDate"]
        category = review_info["videoCategoryValue"]
        duration = review_info["duration"]
        image_url = review_info["thumbnailImageUrl"]
        # if image_url is None:
        #     break
        video_no = review_info["videoNo"]
        image = review_info["image"]
        j = i%col_num
        ctct = ct[j].container(height=475)
        ctct.image(image, width = 500)
        ctct.text("%s [%s] %s\n%s"%(title,category, second_to_strftime(duration), date.split(" ")[0]))
        if ctct.button("채팅 검색하기", key = video_no):
            chat_searching(video_no, duration)
            
    if "review_infos" in st.session_state:
        j = (i+1)%col_num
        ctct = ct[j].container(height=475)
        if st.session_state.page != st.session_state.total_pages-1:
            if ctct.button("이전 영상 더보기", key="before"):
                st.session_state.old_page = st.session_state.page
                st.session_state.page += 1
                st.rerun()
                
        if st.session_state.page != 0:
            if ctct.button("이후 영상 더보기", key="after"):
                st.session_state.old_page = st.session_state.page
                st.session_state.page -= 1
                st.rerun()
        
st.session_state.streamer_no = streamer_no

