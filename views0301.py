# -*- coding: utf-8 -*-
from django.shortcuts import render


from Fapi.models import Fapidb

from Fapi.serializers import FapiSerializer
from Fapi.GCPstorage import GCS

from rest_framework import viewsets, status, request
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
#from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


#import requests, gc
#from bs4 import BeautifulSoup
#from urllib.request import urlopen as uReq

from pandas.core.frame import DataFrame
import datetime
import pandas as pd
from io import StringIO

#待處理事項
#1227
# ok? 1229 1.下載的data 轉成其他種型態 pandas
# 2.RWD板型調整:未切齊邊緣
# ok 1229 3.mail 通知套件使用
# ok? 4.發送post 不變動其他的物件
# 5. google Ad, 或其他廣告方式
#

#0111
#1. scrapy 極度緩慢問題  --> 加強GCP效能,多花錢
#2. 存取下載csv from GCS ok0113
#3. SQL 啟用方法
#4. 定期爬蟲設定 ok?

#0121
#1. 點交, 非點交上線
#1.2 土地篩選

#注意:
#上google cloud 要改 1.Line56 定期抓資料時間 2. pip freeze > requirments.txt 3.改localhost GCP授權的路徑,註解掉
# local host 每次都要 SDK下輸入連線 'cloud_sql_proxy_x64.exe -instances="fapi-264514:asia-east1:fapi-sql"=tcp:3307'

#0215 : 刪減index.html 元件, fapi-views 自動更新關閉, sql cloud 測試連線
#0220 : cloud sql read ok, 新增點交篩選功能, 一些import 改道 def內, sql read print
#0301 : 新增土地scrapy, 地址列增加超連結
#pandas tohtml直接新增
#https://stackoverflow.com/questions/39668851/how-to-create-a-pandas-link-href-style


# Create your views here.
'''
from apscheduler.scheduler import Scheduler
#週期性task 0113
sched = Scheduler()
sched.start()  # 啟動該腳本
@sched.interval_schedule(seconds=60000)
def mytask():
    print('django Scheduler run')
    try:
        GCS.fapiScrapyMain('test')
    except:
        print('update fapi data error')
'''
class FapiViewSets(viewsets.ModelViewSet):
    queryset = Fapidb.objects.all()
    serializer_class = FapiSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    #Ref:
    # http://www.linuxyw.com/276.html
    @csrf_exempt  #關閉django 防html pu post...不安全行為,先關閉
    def menu(request):
        '''
        if request.method == 'POST':
            if request.POST['email']:
                #<QueryDict: {'Num_maxBidValue': ['122202'], 'Num_minBidValue': ['256'], 'CourtName': ['ALL'], 'option': ['Select_NohouseCheck'], 'bt_dfTableRequest': ['']}>

        '''
        return render(request, 'index.html', {'tables': '', 'test' : ''})

    @csrf_exempt
    def update_Manunal(request):
        print('scrapy manunal run')
        GCS.fapiScrapyMain('test')
        return render(request, 'index.html', {'tables': '', 'tx_emailSend': '手動更新CSV到Google Cloud Storage'})

    @csrf_exempt
    def set_fapi(request):
        tx_CourtName, dfTable, test, emailSite, CourtName, emailInfo = '', '', '', '', '', ''
        Select_NohouseCheck = 'Select_houseCheck'

        if request.method == 'GET':
            print(request.GET)
            houseCheck = request.GET['op_houseCheck']
            Num_maxBidValue = request.GET['Num_maxBidValue']
            Num_minBidValue = request.GET['Num_minBidValue']
            if Num_maxBidValue or Num_minBidValue =='':
                render(request, 'index.html', {'tx_emailSend': '請輸入正確的篩選金額'})
            emailSite = request.GET['tx_email']
            Select_NohouseCheck = request.GET['op_houseCheck']
            CourtName = request.GET['op_CourtName']
            op_radio = request.GET['radio_periodChoose']

            radio_periodChoose = ['radio_day', 'radio_week', 'radio_month']

            #print(CourtName, Num_maxBidValue, Num_minBidValue, houseCheck, op_radio, emailSite)

            if op_radio == 'pd_preview':
                print('django fapi pd_preview')
                dfTable = fapiScrap.testReadGCS(CourtName, Num_minBidValue, Num_maxBidValue, houseCheck)
                tx_CourtName = str(fapiScrap.courtNameDict(CourtName))
                #dfTable = fapiScrap.main(CourtName, Num_minBidValue, Num_maxBidValue, Select_NohouseCheck) #只做條件篩選輸出 0109測試註解掉

            if op_radio == 'mail_now':
                if emailSite =='':
                    render(request, 'index.html', {'tx_emailSend': '請輸入正確的e-mail'})
                print('set_emailSite : ' + emailSite + ',' + op_radio)
                test = 'set_emailSite : ' + emailSite + ',' + op_radio  # 回傳網頁值
                # htmldf = fapiScrap.dfReadHtml(CourtName) #測試寫死  讀取網站存放資料 localhost
                fileName = CourtName + '.csv'
                df = fapiScrap.LoadCSVtoDF(fileName)
                df = fapiScrap.dfDropIndex(df)
                today = str(datetime.date.today())
                MailtoUser.sendMail("法拍資訊:" + CourtName + today, "測試ok 1229", df.to_html(classes='data', index=False),
                                    emailSite)  # mail給客戶的資料
                emailInfo = 'email發送至:' + emailSite
                # MailtoUser.sendMail("test", FapiViewSets.set_fapi.dfTable, emailSite)
                # test = emailSite

            if op_radio in radio_periodChoose:

                Fapidb.setuserinfodb(emailSite= emailSite, radio_periodChoose= op_radio, CourtName = CourtName,Select_NohouseCheck=Select_NohouseCheck, Num_maxBidValue= Num_maxBidValue, Num_minBidValue= Num_minBidValue)
                periodChoose = {'radio_day': '每日寄送', 'radio_week': '每週寄送', 'radio_month': '每月寄送'}
                mailInfo = '選擇' + periodChoose[op_radio] + ',SQL資料庫建置中, 暫無定期寄送'
                '''
                原本的except
                emailInfo = '選擇' + periodChoose[op_radio] + ',SQL資料庫建置中, 暫無定期寄送'
                #To period monitor and SQL save user info
                '''

        return render(request, 'index.html', {'tables': dfTable, 'test': tx_CourtName, 'tx_CourtName': tx_CourtName, 'tx_emailSend': emailInfo})

    @csrf_exempt
    def userinfo(request):
        tx_CourtName, dfTable, test, emailSite, CourtName, emailInfo = '', '', '', '', '', ''
        if request.method == 'GET':
            bt_testsql = ''
            # test read cloud sql
            tx_testemail = ''
            tx_testemail = request.GET['tx_testemail']
            dataList = Fapidb.getuserinfo(tx_testemail = tx_testemail, bt_testsql = bt_testsql)
        return render(request, 'index.html', {'tables': dataList})

    '''
    @csrf_exempt
    #只要局部更新不要全部洗掉，put變成get?? 1226
    def set_emailSite(request):
        test, htmldf,  = '',''
        if request.method == 'GET':
            if 'bt_mailRequest' in request.GET:
                emailSite = request.GET['tx_email']
                CourtName = request.GET['op_mailcourtName']
                radio_periodChoose = request.GET['radio_periodChoose']
                print('set_emailSite : ' + emailSite + ',' + radio_periodChoose)
                test = 'set_emailSite : ' + emailSite + ',' + radio_periodChoose #回傳網頁值
                #htmldf = fapiScrap.dfReadHtml(CourtName) #測試寫死  讀取網站存放資料 localhost
                fileName = CourtName + '.csv'
                df = fapiScrap.LoadCSVtoDF(fileName)
                df = fapiScrap.dfDropIndex(df)
                today = str(datetime.date.today())
                MailtoUser.sendMail("法拍資訊:" + CourtName + today, "測試ok 1229", df.to_html(classes='data', index=False), emailSite) #mail給客戶的資料
                #MailtoUser.sendMail("test", FapiViewSets.set_fapi.dfTable, emailSite)
                #test = emailSite
        return render(request, 'index.html', {'tables': '', 'test': '','tx_emailSend': ('email發送至:' + emailSite)})
    '''
    '''
    @csrf_exempt
    #@detail_route(method=['GET'])
    def set_emailSite(self, request, pk=None):
        if request.method == 'GET' and 'bt_mailRequest' in request.GET:
            emailSite = request.GET['tx_email']
            CourtName = request.GET['op_mailcourtName']
            radio_periodChoose = request.GET['radio_periodChoose']
            Num_maxBidValue = request.POST.get('Num_maxBidValue')
            Num_minBidValue = request.POST.get('Num_minBidValue')
            Fapidb.setuserinfodb(emailSite, CourtName, radio_periodChoose, Num_maxBidValue, Num_minBidValue)
        return render(request, "index.html", {'tables': '', 'test': '', 'tx_emailSend': ('email發送至:' + emailSite)})
    '''
    '''
    def bt_mailRequest(request):
        if request.method == 'POST' and request.POST.has_key('bt_mailRequest'):
            MailtoUser.sendMail('test1225', 'nothing to say', 'patrick11041@gmail.com')
    #http://www.youtube.com/channel/UCFj_nVpsvt5v7fARPVMIQLA?sub_confirmation=1   直接訂閱辦法
    '''
class MailtoUser:
    def sendMail(subject, body, htmldf, to_addr):
        from email.mime.text import MIMEText
        import smtplib
        # vbsqufevjocaxbkg
        #https: // stackoverflow.com / questions / 882712 / sending - html - email - using - python
        #mime = MIMEText(body, "plain", "utf-8")  #測試文字
        mime: object = MIMEText(htmldf, 'html', "utf-8")  #轉成mail 格式，給客戶的資料
        #mime = mime.attach(htmlMime)
        mime["Subject"] = subject
        mime["From"] = "Fintech系統 by PNforceStudio"
        mime["To"] = ""
        mime["Cc"] = ""
        #msg = 'Subject:{}\n\n{}'.format(subject, body)
        #msg = mime.as_string()
        msg = mime.as_string()
        smtpssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        # http://yhhuang1966.blogspot.com/2018/10/python-gmail.html
        smtpssl.login("patrick110413@gmail.com", "vbsqufevjocaxbkg")
        from_addr = "patrick110413@gmail.com"
        #msg = "Subject:Gmail sent by Python scripts\nHello World!"
        #msg = 'Subject:{}\n\n{}'.format(subject,body)
        # msg =  "Subjects:testok\n0726testok"
        smtpssl.sendmail(from_addr, to_addr, msg, mail_options=(), rcpt_options=())
        smtpssl.quit()

class fapiScrap: #fapiScrap 應該稱為 fapiSort比較好
    my_url = "http://aomp.judicial.gov.tw/abbs/wkw/WHD2A03.jsp?pageTotal=13&pageSize=15&rowStart=16&saletypeX=1&proptypeX=C52&courtX={}&order=odcrm&query_typeX=session&saleno=&hsimun=all&ctmd=all&sec=all&crmyy=&crmid=&crmno=&dpt=&saledate1=&saledate2=&minprice1=&minprice2=&sumprice1=&sumprice2=&area1=&area2=&registeno=&checkyn=all&emptyyn=all&order=odcrm&owner1=&landkd=&rrange=%A4%A3%A4%C0&comm_yn=&stopitem=&courtNoLimit=&pageNow=15&97166F29649F5A2FE8180AD3FF02C722=D074AEC2F3B4A5BDF2F7EF2E25516A5F"
    projectName = 'fapi'  #GCS專案名稱
    bucketName = 'fapi-tw' #值段名稱, 一個專案對應數個值段存放位置
    '''
    def testPage(courtX):
        url = 'http://aomp.judicial.gov.tw/abbs/wkw/WHD2A03.jsp?pageTotal={}&pageSize=15&rowStart=16&saletypeX=1&proptypeX=C52&courtX={}&order=odcrm&query_typeX=session&saleno=&hsimun=all&ctmd=all&sec=all&crmyy=&crmid=&crmno=&dpt=&saledate1=&saledate2=&minprice1=&minprice2=&sumprice1=&sumprice2=&area1=&area2=&registeno=&checkyn=all&emptyyn=all&order=odcrm&owner1=&landkd=&rrange=%A4%A3%A4%C0&comm_yn=&stopitem=&courtNoLimit=&pageNow={}&97166F29649F5A2FE8180AD3FF02C722=D074AEC2F3B4A5BDF2F7EF2E25516A5F'
        data = []
        for page in range(1, 50):
            url_tmp = url.format('1000', courtX, str(page))  # totalpage不影響輸出, nowpage超過實際的輸出 len = 0 的list
            uClient = uReq(url_tmp)
            page_html = uClient.read()
            uClient.close()
            page_soup = BeautifulSoup(page_html, 'html.parser')  # html parser
            table_ = page_soup.table.find_all('table')[1]
            rows = table_.find_all('tr')
            if len(rows) <= 1:
                print('break')
                break
            s = 0
            if page != 1:
                s = 1
            for i in range(s, len(rows)):
                row = rows[i]
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append(
                    [ele.replace('\r\n', '').replace('\t', '').replace('\n', '').replace('\u3000', '').replace(' ', '')
                     for ele in cols if ele])
            print('scrap page : ' + str(page))
            #print(data)
        return data
    '''
    def dfSaveHtml(df, filename):  #localhost SaveHtml, df is dataframe
        dfhtml = df.to_html()
        today = str(datetime.date.today())  #讀取當日日期加到檔案名
        with open(filename + today + '.html', 'w', encoding="utf-8") as f:
            f.write(dfhtml)
        del dfhtml

    def dfReadHtml(filename): #localhost ReadHtml, return is html
        today = str(datetime.date.today())
        with open(filename+ '.html', 'r', encoding="utf-8") as f:
            return f.read()

    def LoadCSVtoDF(filename, projectName = 'fapi', bucketName = 'fapi-tw', content_type = 'text/csv'):

        print('dfGCSload:' + filename)
        bt = GCS.loadFile(filename, projectName, bucketName, content_type) #讀取雲端csv檔案，定期scrapy的，回bytes
        s = str(bt, 'utf-8') # bytes --> str
        bt = StringIO(s)
        df = pd.read_csv(bt, encoding="UTF-8", index_col=0)  #read_html 回傳list, [0]是dataframe
        return df

    def courtNameDict(CourtName):
        d = {"ALL": "臺灣全部地方法院", "TPD": "臺灣台北地方法院", "PCD": "臺灣新北地方法院", "SLD": "臺灣士林地方法院", "TYD": "臺灣桃園地方法院",
             "SCD": "臺灣新竹地方法院", "MLD": "臺灣苗栗地方法院", "TCD": "臺灣臺中地方法院", "NTD": "臺灣南投地方法院", "CHD": "臺灣彰化地方法院",
             "ULD": "臺灣雲林地方法院", "CYD": "臺灣嘉義地方法院", "TND": "臺灣臺南地方法院", "CTD": "臺灣橋頭地方法院", "KSD": "臺灣高雄地方法院",
             "PTD": "臺灣屏東地方法院", "TTD": "臺灣臺東地方法院", "HLD": "臺灣花蓮地方法院", "ILD": "臺灣宜蘭地方法院", "KLD": "臺灣基隆地方法院",
             "PHD": "臺灣澎湖地方法院", "KMD": "福建金門地方法院", "LCD": "福建連江地方法院"}
        return d[CourtName]

    def courtNameList(self):
        return ["ALL", "TPD", "PCD", "SLD", "TYD", "SCD", "MLD", "TCD", "NTD", "CHD","ULD", "CYD", "TND" "CTD", "KSD","PTD", "TTD", "HLD", "ILD", "KLD", "PHD", "KMD", "LCD"]

    def toDF(data):
        if len(data) != 0:
            df = DataFrame(data)
            df.columns = data[0]  # 這行造成bug需調查
            df = df[1:]
        return df
        
    #關鍵字轉html超連結字串
    def strtoLink(phare,splitword = '號',url = 'https://www.google.com/maps/search/'):    
        urlmap = ['','','']
        a = phare
        urlmap[0] = url
        urlmap[1] = a.split(splitword)[0]
        urlmap[2] = splitword
        a = ''.join(urlmap)
        return a
    
    #df篩選功能
    def dfselection(df, minBidValue, maxBidValue, keyword_cols=[], keyword=['']):
        dfNumIndex = len(df.index)
        df_drop = df
        drop_List = []
        print('keyword filiter')
        for num in range(0, dfNumIndex):
            # print(df.iloc[num,6])
            tempValue = int(str(df.iloc[num, 6]).replace(',', ''))
            # [num,6] y方向第num個, x方向第6欄, 地址是第5欄, 點交第7欄
            # print(str(num),str(df.iloc[num,6]).replace(',',''))

            if tempValue < int(minBidValue) or tempValue > int(maxBidValue):  #金額範圍符合的
                drop_List.append(num + 1)  # List :使用iloc, 第一行資料 index = 0.  #pandas: 第一行資料,index = 1

            if len(keyword_cols) > 0 and len(keyword) > 0:  #有選再做
                for col in range(len(keyword_cols)):  #讀取要篩選的欄位,以這範例為 地址第5欄, 點交第7欄
                    tempValue = str(df.iloc[num, keyword_cols[col]])  #讀取個別欄位值, 例如iloc[10,5]
                    #if keyword[col] != tempValue or keyword[col] not in tempValue: #單詞keyword 比對還有問題
                    if keyword[col] != tempValue:
                        drop_List.append(num+1)  #如果不符合就加入刪去標定list

        df_drop.drop(index=drop_List, inplace=True) #進行刪去標定的橫欄位
        del df
        return df_drop
    '''
    def dfkeywordselection(df, colnum, keyword):
        dfNumIndex = len(df.index)
        df_drop = df
        drop_List = []
        for num in range(0, dfNumIndex):
            # print(df.iloc[num,6])
            tempValue = int(str(df.iloc[num, 6]).replace(',', ''))
        
        return df_drop
    '''

    def dfDropIndex(df_drop):
        return df_drop.drop(['筆次', '法院名稱', '字號股別'], axis=1)

    def dfaddUrl(df):
        dfNumIndex = len(df.index)
        #將地址取出 .split('號')，合併 '"google.com.tw//maps//place//" + 取出地址 + "/" '
        return df


    def main(courtName,Num_minBidValue=1000000,Num_maxBidValue=5000000,houseCheck='Check'):
        data = fapiScrap.testPage(courtName)  # 取得全list
        df = fapiScrap.toDF(data)  # 轉pandas
        fapiScrap.dfSaveHtml(df, str(courtName)) #存在localhost ,同一資料夾下
        df = fapiScrap.dfselection(df, int(Num_minBidValue), int(Num_maxBidValue))  # dataframe 篩選
        df = fapiScrap.dfDropIndex(df)
        return df.to_html(classes='data', index=False)
    
    
    
    #網頁板主要輸出功能
    def testReadGCS(courtName,Num_minBidValue=1000000,Num_maxBidValue=5000000,houseCheck='All',keyword=''):
        #點交篩選
        filename = courtName + '.csv'
        content_type = ''
        print('testReadGCS : ' + filename)
        df = fapiScrap.LoadCSVtoDF(filename)

        if houseCheck == 'All' and keyword == '':
            df = fapiScrap.dfselection(df, int(Num_minBidValue), int(Num_maxBidValue))  # dataframe 篩選
        elif keyword =='':
            cl = ['不點交'] if houseCheck == 'NoCheck' else ['點交']
            keyloc = [7]
            df = fapiScrap.dfselection(df, int(Num_minBidValue), int(Num_maxBidValue), keyloc, cl)
        else:
            cl = ['不點交'] if houseCheck == 'NoCheck' else ['點交']
            cl.insert(0,keyword)
            keyloc = [5,7]
            df = fapiScrap.dfselection(df, int(Num_minBidValue), int(Num_maxBidValue), keyloc, cl)
        # dataframe 篩選
        df = fapiScrap.dfDropIndex(df)
        return df.to_html(classes='data', index=False)

