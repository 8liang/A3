#!/usr/local/bin/python
# -*- coding: UTF-8 -*-
import ConfigParser
import xlrd
import csv
import pymssql
import time
import sys
reload(sys)
sys_type = sys.getfilesystemencoding()
sys.setdefaultencoding('utf-8')
config = ConfigParser.ConfigParser()
config.readfp(open('config.ini'))
db_config = config.items('DB')
# sa
# Aa12345
#GetMaxID 生成memberId
#GetOrderID 生成订单Id

fields = {'origin_id':0,'name':5, 'phone':6, 'address':7}
csv_fields = ('origin_id','product','product_id','product_code','amount','price','freight','pay_type',
'name','phone','address','province','city','district','address_in_detail','remark','placed_at','finished_at',
'express_co','express_order_id')

conn = pymssql.connect(
	host=config.get('DB', 'host'),
	user=config.get('DB', 'username'),
	password=config.get('DB', 'password'),
	database=config.get('DB', 'db_name'),
	autocommit=True
	)

def print_s(str):
	print(str.decode('utf-8').encode(sys_type))

def load_csv(file_name):
	datas = []
	with open(file_name) as csvfile:
		reader = csv.DictReader(csvfile, csv_fields)
		next(reader)
		for row in reader:
			row['origin_id'] = row['origin_id'].lstrip("'")
			datas.append(row)
	return datas

def load_execel(file_name):
	datas = []
	data = xlrd.open_workbook(file_name)
	table = data.sheets()[0]
	for i in range(1, table.nrows):
		row = {}
		for obj in fields.items():
			k, v = obj
			row[k] = table.cell_value(i, v)
		if not row['name'].strip():
			break
		datas.append(row)
	return datas

def enc_tel(tel):
	sql = "SELECT dbo.EncTel(%s)"%tel
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	return result[0]

def dec_tel(tel):
	sql = "SELECT dbo.DecTel(\'%s\')"%tel
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	return result[0]

def generate_member_id(employee_id):
	sql = "DECLARE @ID BIGINT EXEC dbo.GetMaxID @EmployeeID=%d,@MaxID=@ID OUTPUT SELECT @ID"%employee_id
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	return result[0]

def generate_product_id():
	sql = "SELECT MAX(ProductID) FROM info_Product"
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	return result[0]+1

def get_product_id(product, price):
	product = product.strip()
	sql = "SELECT ProductID FROM info_Product WHERE ProductName='%s'"%product
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	if result:
		return result[0]
	id = generate_product_id()
	code = 1010000+id
	now = time.strftime("%Y-%m-%d %H:%M:%S")
	data = {
		'ProductID':'%d'%id,
		'ProductCode':'0%d'%code,
		'ProductName':product,
		'SupplierID':'3',
		'TypeID':'8',
		'ProductPrice':price,
		'CreateDate':now,
		'UpdateDate':now,
		'isalemarker':'1',
		'StockPrice':price,
	}
	insert_into('info_Product', data)
	return id

def generate_order_id(employee_id):
	sql = "DECLARE @ID VARCHAR(200) EXEC dbo.GetOrderID @PayTypeID=1, @SaleID=%d,@sOrderID=@ID OUTPUT SELECT @ID"%employee_id
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	return result[0]

def get_member_id(phone, name, address):
	sql = "SELECT MemberID FROM info_PhoneList WHERE PhoneNum=dbo.EncTel('%s')"%phone
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	if result:
		return result[0]

	member_id = generate_member_id(1)
	encPhone = enc_tel(phone)
	insert_into('info_PhoneList', {
		'MemberId':'%d'%member_id,
		'PhoneNum':encPhone,
		'IsKeyNum':'1',
		'PhoneNumStar':phone
	})
	now = time.strftime("%Y-%m-%d %H:%M:%S")


	insert_into('info_MemberBasic', {
		'MemberID':'%d'%member_id,
		'MemberName':name,
		'Homephone':encPhone,
		'Mobile':encPhone,
		'OtherPhone':encPhone,
		'DetailAddress':address,
		'MemberTypeID':'2', 
		'LastDatetime':now,
		'AddDate':now,
		'CheckDateTime':now,
		'LastUpdateTime':time.strftime("%y%m%d%H%M%S100"),
		'LastSeatNumber':'1',
		'ConsultProductID':'1',
		'MemSource2':'1'
	})
	return member_id

def insert_into(table, o):
	value_sql = "','".join(o.values()) + "')"
	sql = 'INSERT INTO ' + table + ' (' + ','.join(o.keys()) +') VALUES (\'' +  value_sql
	cursor = conn.cursor()
	cursor.execute(sql)
	
def generate_order_product(order, row):
	sql = 'SELECT * FROM info_product WHERE ProductID=%s'%order['ConsultProductID']
	cursor = conn.cursor(as_dict=True)
	cursor.execute(sql)
	result = cursor.fetchone()
	data = {
		'SaleID':order['SaleID'],
		'ProductID':order['ConsultProductID'],
		'productcode':result['ProductCode'],
		'ProductName':result['ProductName'],
		'Unit':'默认',
		'Price':'%f'%result['ProductPrice'],
		'Amount':row['amount'],
		'subTotal': '%d'%(int(row['amount']) * result['ProductPrice']),
		'SalePrice':'%f'%result['ProductPrice'],
		'ProductTypeID':'1',
		'ProductTypeName':'正品',
		'TypeID':'%d'%result['TypeID'],
		'TypeName':'商品',
		'IsSequelSell':'否',
		'IsTieinSell':'否'
	}
	insert_into('thing_OrderProduct', data)

def generate_order_after(o):
	del o['OrderID']
	del o['MediaTypeID']
	del o['GetMoney']
	del o['PlanSendGoodDate']
	del o['FreightMoney']
	del o['TotalMoney']
	del o['TicketMoney']
	del o['DisCountMoney']
	del o['PayMoney']
	del o['UserCoupons']
	del o['StoreMoney']
	insert_into('thing_OrderBasicAfter', o)

def generate_order_status(order, row):
	now = time.strftime("%Y-%m-%d %H:%M:%S")
	data = {
		'SaleID':order['SaleID'],
		'OrderID':order['OrderID'],
		'BeginDepartID':'1',
		'CurrentDepartID':'5',
		'OrderStatus':'501',
		'OrderDate':order['OrderDate'],
		'CancelStatus':'401',
		'FinaCheckDate':now,
		'GoodCheckDate':now,
		'GoodCheckManID':'1',
		'FinaMoneyDate':now,
		'LastUpdateTime':time.strftime("%y%m%d%H%M%S100")
	}
	insert_into('thing_OrderStatus', data)

def generate_order_success(order, row):
	data = {
		'SaleID':order['SaleID'],
		'PayTypeID':'1',
		'BankID':'0',
		'TicketFlag':'0',
		'SendDetailAddress':row['address'],
		'ReceiveMan':row['name'],
		'ContactMobile':enc_tel(row['phone']),
		'ContactAllStar':row['phone'],
		'note':row['origin_id'],
		'TicketMemo':row['origin_id']
	}
	insert_into('thing_OrderSuccess', data)

def import_single(row):
	now = time.strftime("%Y-%m-%d %H:%M:%S")
	if not row['origin_id']:
		print_s('记录格式或顺序不正确')
		return
	sql = "SELECT * FROM FL_Marks WHERE id='%s'"%row['origin_id']
	cursor = conn.cursor()
	cursor.execute(sql)
	result = cursor.fetchone()
	if result:
		print_s('单号[%s]已经在(%s)导入过了'%(row['origin_id'],result[1]))
		return

	member_id = get_member_id(row['phone'], row['name'], row['address'])
	sale_id = generate_member_id(1)
	order_id = generate_order_id(sale_id)
	
	o = {
		'SaleID':'%d'%sale_id,
		'OrderID':order_id,
		'MemberFlag':'2',
		'MemberID':'%d'%member_id,
		'PhoneTypeID':'2',
		'ConsultProductID':'%d'%get_product_id(row['product'], row['price']),
		'EmployeeID':'1',
		'OperatorID':'1',
		'OrderDate':row['finished_at'],
		'VisitEmployeeID':'1',
		'TannelID':'8',
		'CheckDate':now,
		'AllReason':'订购',
		'CallBackTime':now,
		'EditTime':now,
		'EditorID':'1',
		'DispatchDetailID':'1',
		'UseMoney':'0',
		'StoreMoney':'0',
		'GetMoney':'0',
		'UserCoupons':'0',
		'VisitFlag':'1',
		'PoundageMoney':'0',
		'PlanSendGoodDate':now,
		'TicketMoney':'0',
		'TotalMoney':'%s'%row['price'],
		'MediaTypeID':'8',
		'FreightMoney':'0',
		'DisCountMoney':'0',
		'PayMoney':'%s'%row['price'],
		'Memo':row['origin_id']
	}
	insert_into('thing_OrderBasic', o)
	generate_order_product(o, row)
	generate_order_status(o, row)
	generate_order_success(o, row)
	insert_into('FL_Marks', {'id':row['origin_id'], 'created_at':now})


datas = load_csv(config.get('PATH', 'csv_name'))
for row in datas:
	if row['amount'] == '1':
		get_product_id(row['product'], row['price'])
for row in datas:
	import_single(row)