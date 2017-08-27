#!/usr/bin/env python

import selenium.webdriver as webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys
from time import sleep 

# browser = webdriver.Firefox()
# browser.get('https://www.google.com?q=python#q=python')
# first_result = ui.WebDriverWait(browser, 15).until(lambda browser: browser.find_element_by_class_name('rc'))
# first_link = first_result.find_element_by_tag_name('a')
# 
# # Save the window opener (current window, do not mistaken with tab... not the same)
# main_window = browser.current_window_handle
# 
# # Open the link in a new tab by sending key strokes on the element
# # Use: Keys.CONTROL + Keys.SHIFT + Keys.RETURN to open tab on top of the stack 
# first_link.send_keys(Keys.COMMAND + Keys.RETURN)
# 
# sleep(2)
# 
# # Put focus on current window which will, in fact, put focus on the current visible tab
# browser.switch_to_window(browser.window_handles[-1])
# 
# 
# # do whatever you have to do on this page, we will just got to sleep for now
# sleep(2)
# 
# # Close current tab
# browser.close()
# 
# # Put focus on current window which will be the window opener
# browser.switch_to_window(main_window)

def create_browser():
	return webdriver.Firefox() # Change browser here

def play_new_video(browser, link):
	browser.get("{}".format(link))
	player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
	while player_status:
		sleep(1)
		player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")


video_list = ['https://www.youtube.com/watch?v=ae5XaKFm2og',
			  'https://www.youtube.com/watch?v=PC58uFFiLHM',
			  'https://www.youtube.com/watch?v=x_UHvprwpVE']

browser = create_browser()
for link in video_list:
	play_new_video(browser, link)


# browser = create_browser()
# browser.get('https://www.youtube.com/watch?v=ae5XaKFm2og')
# 
# # Save the window opener (current window, do not mistaken with tab... not the same)
# main_window = browser.current_window_handle
# 
# 
# video_list = ['https://www.youtube.com/watch?v=ae5XaKFm2og',
# 			  'https://www.youtube.com/watch?v=PC58uFFiLHM',
# 			  'https://www.youtube.com/watch?v=x_UHvprwpVE']
# player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
# 
# while player_status:
# 	sleep(1)
# 	player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
# 
# print "video is done"