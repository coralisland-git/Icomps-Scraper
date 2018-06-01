# from __future__ import unicode_literals
import scrapy

import json

import csv

import os

import scrapy

from scrapy.spiders import Spider

from scrapy.http import FormRequest

from scrapy.http import Request

from chainxy.items import ChainItem

from selenium import webdriver

from pyvirtualdisplay import Display

import random

from lxml import etree

import time

import MySQLdb

import sys

import pdb


class Icomps(scrapy.Spider):

	name = 'Icomps'

	domain = 'https://www.icomps.com'

	proxy_list = []

	choice = ''

	def __init__(self):

		# self.driver = webdriver.Chrome("./chromedriver")

		script_dir = os.path.dirname(__file__)

		file_path = script_dir + '/data/proxy list.txt'

		with open(file_path, 'rb') as text:

			content = text.readlines()

		for proxy in content :

			proxy = proxy.replace('\n', '')

			proxy = 'http://' + proxy

			self.proxy_list.append(proxy)


		self.headers = [

			"folio", "pin", "owner", "owner_addr", "owner_city", "owner_state", "owner_zip", "site_addr", "site_city", "site_state", "site_zip", "bed", "bath", "square_footage", "zestimate", "active", "icomps", "redfin", "trulia"

		]


		db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="zillow_db")       

		self.cur = db.cursor()


	def start_requests(self):

		yield scrapy.Request(self.domain, callback=self.parse_case,  meta={'proxy' : random.choice(self.proxy_list) }, dont_filter=True)


	def parse_case(self, response):

		print("""
--------- Options ---------

	0 : Csv

	1 : Icomps
---------------------------
			""")
		
		self.choice = raw_input(' Select : ')

		try:

			self.choice = int(self.choice)

		except:

			self.choice = -1


		if self.choice == 0:

			yield scrapy.Request(self.domain, callback=self.parse_csv, meta={'proxy' : random.choice(self.proxy_list) }, dont_filter=True)

		elif self.choice == 1:

			sql = "select * from parcel_estimate where icomps is NULL or icomps='0' or icomps=''"

			self.cur.execute(sql)

			rows = self.cur.fetchall()

			for row in rows:

				item = ChainItem()

				for ind in range(0, len(row)-1):

					item[self.headers[ind].title()] = row[ind+1]

				url = 'https://icomps.com/'

				headers = {

					'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',

					'Accept-Encoding':'gzip, deflate, br',

					'Content-Type':'multipart/form-data; boundary=----WebKitFormBoundaryEA6WIdnFYAG0Pxrw',

					'Upgrade-Insecure-Requests':'1'

				}

				formdata = {

					'address' : item['Site_Addr'] + ', ' + item['Site_City'] + ', ' + item['Site_State']

				}

				yield scrapy.FormRequest(url, callback=self.parse_icomps, formdata=formdata , method='POST', meta={ 'item' : item, 'proxy' : random.choice(self.proxy_list)}, dont_filter=True)

		else:

			print(' ~~~~ Warning! : invalid format ~~~')


	def parse_csv(self, response):

		count = 0

		script_dir = os.path.dirname(__file__)

		file_path = script_dir + '/data/HC_ALL_SFR.csv'

		with open(file_path, 'rb') as csvfile:

			spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')

			for row in spamreader:

				if count >= 1:

					item = ChainItem()

					for ind in range(0, len(row)):

						item[self.headers[ind].title()] = row[ind].replace('"', '')

					sql = "select * from parcel_estimate where folio=%s" %item['Folio']

					self.cur.execute(sql)

					rows = self.cur.fetchall()

					if len(rows) == 0:
				
						yield item

				count += 1


	def parse_icomps(self, response):		

		if 'comparables' in response.body.lower() : 

			print('warning : Icomps.com went down. please try again later.')

		else:

			item = response.meta['item']

			try:

				item['Icomps'] = self.validate(''.join(response.xpath('//p[contains(@class, "green value")]//text()').extract()).split(':')[1].strip().replace('$', '').replace(',',''))

			except :

				item['Icomps'] = ''

			yield item


	def validate(self, item):

		try:

			return item.replace('\n', '').replace('\t','').replace('\r', '').strip()

		except:

			pass
			

	def eliminate_space(self, items):

		tmp = []

		for item in items:

			if self.validate(item) != '':

				tmp.append(self.validate(item))

		return tmp