import pygame as pg
import os
from random import choice
import boto3
from time import time


os.environ['SDL_VIDEO_CENTERED'] = '1'
pg.init()

reg, key, access = '', '', ''
with open('creds.txt', 'r') as file:
	creds = file.read().split('\n')
	reg = creds[0]
	key = creds[1]
	access = creds[2]

dynamodb = boto3.resource(
    'dynamodb',
    region_name=reg,
    aws_access_key_id=key,
    aws_secret_access_key=access,
)

width, height = 730, 730
w2, h2 = width / 2, height / 2
screen = pg.display.set_mode((width, height))
icon = pg.image.load("bingoD.png")
pg.display.set_icon(icon)
fonts = {'18': pg.font.Font('seguisym.ttf', 18), '26': pg.font.Font('seguisym.ttf', 26), '48': pg.font.Font('seguisym.ttf', 48)}

roomkey = ''
numList = [0 for _ in range(25)]
circled = [0 for _ in range(25)]
bingo = 0
player = 0

BACK = (50, 50, 50)
GREEN = (48, 141, 70)
GREEND = (44, 74, 51)


def addText(font, sent, color, y, x=None, xoff=None, nxoff=None):
	text = font.render(sent, True, color)
	textRect = text.get_rect()
	if x:
		textRect.center = (x, y)
	if xoff:
		textRect.center = (xoff + textRect.width / 2, y)
	if nxoff:
		textRect.center = (width - nxoff - textRect.width / 2, y)
	screen.blit(text, textRect)


def roomKeyGen():
	with open('words.txt', 'r') as file:
		words = file.read()

	word = choice(words.split('\n'))
	try:
		word = dynamodb.Table('game').get_item(Key={'roomkey':word})['Item']['roomkey']
		return None
	except:
		dynamodb.Table('game').put_item(Item={'roomkey':word, 'players':1, 'turn':1, 'filled':'00', 'circled':'', 'won':0})
		return word
	

def findRoomKey(key):
	try:
		_ = dynamodb.Table('game').get_item(Key={'roomkey':key})['Item']['roomkey']
		updateRoom(key, 'players', 1)
		return True
	except:
		return False


def getRoom(key, att):
	return dynamodb.Table('game').get_item(Key={'roomkey':key})['Item'][att]


def updateRoom(key, att, val):
	if att == 'players':
		pl = getRoom(key, 'players')
		val += pl

	dynamodb.Table('game').update_item(Key={'roomkey':key}, UpdateExpression=f'set {att} =:X', ExpressionAttributeValues={":X":val})


def mainPage(join=False, tempkey=None, blink=True):
	if join:
		pg.draw.line(screen, GREEN, (w2 - 85, h2), (w2 + 85, h2), 2)
		if blink:
			addText(fonts['26'], tempkey + '|', GREEN, h2 - 25, width / 2)
		else:
			addText(fonts['26'], tempkey, GREEN, h2 - 25, width / 2)
		pg.draw.rect(screen, GREEN, pg.Rect(w2 - 85, h2 + 10, 170, 50), 2, 3)
		addText(fonts['26'], 'Join', GREEN, h2 + 35, width / 2)
	else:
		pg.draw.rect(screen, GREEN, pg.Rect(w2 - 85, h2 - 60, 170, 50), 2, 3)
		addText(fonts['26'], 'Create Room', GREEN, h2 - 35, width / 2)
		pg.draw.rect(screen, GREEN, pg.Rect(w2 - 85, h2 + 10, 170, 50), 2, 3)
		addText(fonts['26'], 'Join Room', GREEN, h2 + 35, width / 2)


def roomPage():
	addText(fonts['18'], f'Room: {roomkey}', GREEN, 20, xoff=15)
	addText(fonts['18'], f'Player: {player}', GREEN, 20, nxoff=15)
	clicked()

	pg.draw.rect(screen, GREEN, pg.Rect(w2 - 250, h2 - 250, 500, 500), 2, 3)

	pg.draw.line(screen, GREEN, (w2 - 150, h2 - 250), (w2 - 150, h2 + 250), 2)
	pg.draw.line(screen, GREEN, (w2 - 50, h2 - 250), (w2 - 50, h2 + 250), 2)
	pg.draw.line(screen, GREEN, (w2 + 50, h2 - 250), (w2 + 50, h2 + 250), 2)
	pg.draw.line(screen, GREEN, (w2 + 150, h2 - 250), (w2 + 150, h2 + 250), 2)

	pg.draw.line(screen, GREEN, (w2 - 250, h2 - 150), (w2 + 250, h2 - 150), 2)
	pg.draw.line(screen, GREEN, (w2 - 250, h2 - 50), (w2 + 250, h2 - 50), 2)
	pg.draw.line(screen, GREEN, (w2 - 250, h2 + 50), (w2 + 250, h2 + 50), 2)
	pg.draw.line(screen, GREEN, (w2 - 250, h2 + 150), (w2 + 250, h2 + 150), 2)

	addText(fonts['48'], 'B', GREEN, h2 - 200, w2 - 300)
	addText(fonts['48'], 'I', GREEN, h2 - 100, w2 - 300)
	addText(fonts['48'], 'N', GREEN, h2, w2 - 300)
	addText(fonts['48'], 'G', GREEN, h2 + 100, w2 - 300)
	addText(fonts['48'], 'O', GREEN, h2 + 200, w2 - 300)

	for i in range(25):
		if numList[i] != 0:
			addText(fonts['48'], f'{numList[i]}', GREEN, h2 - 200 + (100 * (i // 5)), w2 - 200 + (100 * (i - (5 * (i // 5)))))


def clicked():
	for i in range(25):
		if circled[i] == 1:
			x = numList.index(i + 1)
			pg.draw.rect(screen, GREEND, pg.Rect(w2 - 250 + (100 * (x - (5 * (x // 5)))), h2 - 250 + (100 * (x // 5)), 100, 100), 0)


def check(player):
	global bingo
	bingo = 0
	offset = 30
	w = 10
	numcircle = [0 for _ in range(25)]
	
	for i in range(25):
		numcircle[i] = circled[numList[i] - 1]

	for i in range(0, 25, 5):
		if 0 not in numcircle[i:i + 5]:
			bingo += 1

	for i in range(5):
		if 0 not in [numcircle[i + j] for j in range(0, 21, 5)]:
			bingo += 1

	if 0 not in [numcircle[0], numcircle[6], numcircle[12], numcircle[18], numcircle[24]]:
		bingo += 1

	if 0 not in [numcircle[4], numcircle[8], numcircle[12], numcircle[16], numcircle[20]]:
		bingo += 1

	if bingo >= 1:
		pg.draw.line(screen, GREEND, (w2 - 300 - offset, h2 - 200 - offset), (w2 - 300 + offset, h2 - 200 + offset), w)
	if bingo >= 2:
		pg.draw.line(screen, GREEND, (w2 - 300 - offset, h2 - 100 - offset), (w2 - 300 + offset, h2 - 100 + offset), w)
	if bingo >= 3:
		pg.draw.line(screen, GREEND, (w2 - 300 - offset, h2 - offset), (w2 - 300 + offset, h2 + offset), w)
	if bingo >= 4:
		pg.draw.line(screen, GREEND, (w2 - 300 - offset, h2 + 100 - offset), (w2 - 300 + offset, h2 + 100 + offset), w)
	if bingo >= 5:
		pg.draw.line(screen, GREEND, (w2 - 300 - offset, h2 + 200 - offset), (w2 - 300 + offset, h2 + 200 + offset), w)
		updateRoom(roomkey, 'won', player)


def runGame():
	global roomkey, numList, circled, player
	player = 0
	turn = 1
	k = 1
	join = False
	tempKey = ''
	filled = ''
	blink = True
	won = 0

	start = time()
	run = True
	while run:
		screen.fill(BACK)

		for event in pg.event.get():
			try:
				turn = getRoom(roomkey, 'turn')
				won = getRoom(roomkey, 'won')
			except:
				pass
			if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
				pg.quit()
				run = False
				break

			if won == 0:
				if join:
					if event.type == pg.KEYDOWN:
						if event.key == pg.K_BACKSPACE and tempKey != '':
							tempKey = tempKey[:-1]
						elif len(tempKey) < 9 and (str(event.unicode).isalpha() or str(event.unicode).isdigit()):
							tempKey += str(event.unicode).upper()
						elif event.key == pg.K_RETURN:
							if findRoomKey(tempKey):
								roomkey = tempKey
								player = 2

				if roomkey == '':
					if join:
						if w2 - 85 < pg.mouse.get_pos()[0] < w2 + 85 and h2 - 40 < pg.mouse.get_pos()[1] < h2:
							pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
						elif w2 - 85 < pg.mouse.get_pos()[0] < w2 + 85 and h2 + 10 < pg.mouse.get_pos()[1] < h2 + 60:
							pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
							if event.type == pg.MOUSEBUTTONUP and tempKey != '':
								if findRoomKey(tempKey):
									roomkey = tempKey
									player = 2
						else:
							pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
					else:
						if w2 - 85 < pg.mouse.get_pos()[0] < w2 + 85 and h2 - 60 < pg.mouse.get_pos()[1] < h2 - 10:
							pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
							if event.type == pg.MOUSEBUTTONUP:
								while roomkey == '':
									tempRoomKey = roomKeyGen()
									if tempRoomKey:
										roomkey = tempRoomKey

								player = 1
								print(f'Key: {roomkey}')

						elif w2 - 85 < pg.mouse.get_pos()[0] < w2 + 85 and h2 + 10 < pg.mouse.get_pos()[1] < h2 + 60:
							pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
							if event.type == pg.MOUSEBUTTONUP:
								join = True
						else:
							pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
				else:
					if 0 in numList:
						pos = (pg.mouse.get_pos()[0] - 115) // 100, (pg.mouse.get_pos()[1] - 115) // 100
						if event.type == pg.MOUSEBUTTONUP and 0 <= pos[0] <= 4 and 0 <= pos[1] <= 4 and numList[pos[1] * 5 + pos[0]] == 0:
							numList[pos[1] * 5 + pos[0]] = k
							k += 1
					else:
						if filled != '11':
							filled = getRoom(roomkey, 'filled')
							if player == 1:
								if filled[0] != '1':
									updateRoom(roomkey, 'filled', f'1{filled[1]}')
							elif player == 2:
								if filled[1] != '1':
									updateRoom(roomkey, 'filled', f'{filled[0]}1')
						else:
							pos = (pg.mouse.get_pos()[0] - 115) // 100, (pg.mouse.get_pos()[1] - 115) // 100
							circ = getRoom(roomkey, 'circled')
							if event.type == pg.MOUSEBUTTONUP and 0 <= pos[0] <= 4 and 0 <= pos[1] <= 4 and turn == player:
								if circled[numList[pos[1] * 5 + pos[0]] - 1] == 0:
									circled[numList[pos[1] * 5 + pos[0]] - 1] = 1
									if circ == '':
										updateRoom(roomkey, 'circled', f'{numList[pos[1] * 5 + pos[0]]}')
									else:
										updateRoom(roomkey, 'circled', f'{circ} {numList[pos[1] * 5 + pos[0]]}')
									updateRoom(roomkey, 'turn', player % 2 + 1)
							else:
								if circ != '':
									for i in circ.split(' '):
										circled[int(i) - 1] = 1

		if run:
			if won == 0:
				if roomkey == '':
					if time() - start > 0.75:
						blink = not blink
						start = time()
					
					mainPage(join, tempKey, blink)
				else:
					roomPage()

				check(player)

				pg.display.update()
			else:
				roomPage()
				check(player)
				addText(fonts['48'], f'Player {won} won!', GREEN, height - 50, w2)
				pg.display.update()



if __name__ == '__main__':
	runGame()
	updateRoom(roomkey, 'players', -1)

	if getRoom(roomkey, 'players') == 0:
		dynamodb.Table('game').delete_item(Key={'roomkey':roomkey})