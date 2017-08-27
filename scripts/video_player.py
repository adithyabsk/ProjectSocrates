def create_browser():
	return webdriver.Firefox() # Change browser here

def play_new_video(browser, link):
	browser.get("{}".format(link))
	player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
	while player_status:
		sleep(1)
		player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")


video_list = ['ADD_VIDEO_URLS_HERE',
			  'ADD_VIDEO_URLS_HERE',
			  'ADD_VIDEO_URLS_HERE']

browser = create_browser()
for link in video_list:
	play_new_video(browser, link)


def main():
	pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit = 1
        raise