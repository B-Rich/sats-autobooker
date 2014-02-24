#!/usr/bin/env python
#coding=utf-8

import urllib, urllib2, cookielib, json, codecs, sys
from datetime import datetime
from sets import Set

def readconfig(filename):
	f = codecs.open(filename, 'r', 'utf-8');
	lines = f.readlines()
	classes = [];
	for line in lines:
		if line.startswith('email'):
			email = line.split('=', 1)[1].strip()
		elif line.startswith('password'):
			password = line.split('=', 1)[1].strip()
		elif line.startswith('#'):
			continue
		else:
			class_array = map(lambda(x): x.strip(), line.split(','))
			if len(class_array) == 3:
				class_config = {}
				class_config['what'] = class_array[0]
				class_config['when'] = class_array[1]
				class_config['where'] = class_array[2]
				classes.append(class_config)
	return (email, password, classes)

def search_for_classes(opener, centers, classes):
	search_centers = Set(map(lambda(x): x['where'], classes))

	search_center_ids = []
	for center in centers :
		if center['Name'] in search_centers:
			search_center_ids.append(str(center['ID']))

	# search through all classes 14 days from now
	search = {
		'day':'14',
		'time':'05:00-09:00,09:00-11:00,11:00-13:00,13:00-17:00,17:00-22:00',
		'category':'undefined',
		'region':'undefined',
		'instructor':'',
		'classes':'',
		'classMode':'all',
		'centerMode':'favorite',
		'instructorMode':'all',
		'dayMode':'undefined'
	}
	search['center'] = ",".join(search_center_ids)

	search_data = urllib.urlencode(search)

	print "Loading potential classes..."
	resp = opener.open('https://www.sats.se/api/sv-SE/booking/search', search_data)
	return json.load(resp)['List']

def string_to_iso_week_day(string):
	m = {u'Måndag' : 1, u'Tisdag' : 2, u'Onsdag' : 3, u'Torsdag' : 4, u'Freday' : 5, u'Lördag' : 6, u'Söndag' : 7 }
	return m[string]

def same_time(iso_day_time, when):
	day_time = datetime.strptime(iso_day_time, "%Y-%m-%d %H:%M:%S")
	if day_time.isoweekday() != string_to_iso_week_day(when.split(' ')[0]):
		return False
	time = when.split(' ')[1]
	if datetime.strftime(day_time, "%H:%M") != time:
		return False
	return True

def book_class(opener, class_to_book):
	class_id = class_to_book['ID']
	booking = { 'classId' : class_to_book['ID'] }
	booking_data = urllib.urlencode(booking)
	print "Booking class " + str(class_to_book) + "..."
	resp = opener.open('https://www.sats.se/api/sv-SE/booking/book', booking_data)

def class_in_class_list(candidate_class, classes_to_book):
	for class_to_book in classes_to_book:
		if (candidate_class['Class'] == class_to_book['what'] and
				same_time(candidate_class['StartTimeDate'], class_to_book['when']) and
				candidate_class['Center'] == class_to_book['where']):
			return True
	return False

def log_in(opener, email, password):
	login_data = urllib.urlencode({'email' : email, 'password' : password, 'rememberme' : 'on'})
	print "Logging in..."
	resp = opener.open('https://www.sats.se/login', login_data)

def load_list_of_centers(opener):
	print "Requesting list of centers..."
	resp = opener.open('https://www.sats.se/api/sv-SE/booking/init/init?apiver=2')
	return json.load(resp)['Centers']

def book_matching_classes(search_results, classes):
	for cl in search_results[0]['Classes']:
		if class_in_class_list(cl, classes):
			if cl['Booked']:
				print "Already booked " + cl['Class'] + " on " + cl['StartTimeDate'] + " at " + cl['Center']
			else:
				book_class(opener, cl)

def main():
	# enable safer printing
	UTF8Writer = codecs.getwriter('utf8')
	sys.stdout = UTF8Writer(sys.stdout)

	(email, password, classes) = readconfig('sats.config')

	cookie_jar = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))

	log_in(opener, email, password)

	centers = load_list_of_centers(opener)

	search_results = search_for_classes(opener, centers, classes)

	book_matching_classes(search_results, classes)

main()
