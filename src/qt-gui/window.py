from PyQt5.QtCore import *
from PyQt5.QtWidgets import * 
import genlist_api
from ui_window import Ui_Window
from pandas import DataFrame
import re
import sqlite3
import codecs
import csv

class Window(QWidget, Ui_Window):
    
    def __init__(self, parent = None):
        super(Window, self).__init__()
        #QWidget.__init__(self, parent)
        self.setupUi(self)
        self.butBlist.clicked.connect(self.browBaselist)
        self.butSlist.clicked.connect(self.browSlist)
        self.butAddToTree.clicked.connect(self.addToTree)
        self.lineSpecies.returnPressed.connect(self.addToTree)
        self.butGenerateSp.clicked.connect(self.genNamelist)
        self.butSelectTempFile.clicked.connect(self.browTempfile)
        self.butSelectOutput.clicked.connect(self.browOutput)
        self.butDeleteAll.clicked.connect(self.delAllTreeItems)
        self.butDeleteSelection.clicked.connect(self.delSelectedItems)
        self.comboDBselect.activated.connect(self.loadSelectedTable)
        try:
            g = genlist_api.Genlist()
            completer = QCompleter()
            self.lineSpecies.setCompleter(completer)
            model = QStringListModel()
            completer.setModel(model)
            retrieved = g.dbGetsp('dao_pnamelist_apg3')        
            b_container=[]
            for i in range(len(retrieved)):
                b_container.append(retrieved[i][3] +  "," + retrieved[i][4] + "," + retrieved[i][2])
            model.setStringList(b_container)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
            

        #for 
        #completer = QCompleter()
        #self.lineSpecies.setCompleter(completer)
        #model = QStringListModel()
        #completer.setModel(model)
        #self.getCompleteData(model, Blist)



    def browBaselist(self):
        """
        browBaselist: browse the baselist file 
        ======================================
        """
        try:
            self.lineBlist.clear()
            Blist = QFileDialog.getOpenFileName(self, self.tr("Open File 開啟物種資料檔案:"), QDir.homePath(), self.tr("Text files (*.txt *.csv)"))[0]
            if Blist is '' or Blist is None:
                return
            else:
                self.lineBlist.setText(Blist) 
                completer = QCompleter()
                self.lineSpecies.setCompleter(completer)
                model = QStringListModel()
                completer.setModel(model)
                self.getCompleteData(model, Blist)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 
    def checkDB(self):
        try:
            db_idx = self.comboDBselect.currentIndex()
            if db_idx == 0:
                db_table = 'dao_pnamelist_apg3'
            elif db_idx == 1:
                db_table = 'dao_pnamelist'
            elif db_idx == 2:
                db_table = 'dao_bnamelist'
            else:
                db_table = 'dao_pnamelist'
            return(db_table)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))


    def browSlist(self):
        try:
            self.lineSlist.clear()
            Slist = QFileDialog.getOpenFileName(self, self.tr("Open File 開啟物種清單檔案:"), QDir.homePath(), self.tr("Text files (*.txt *.csv)"))[0]
            if Slist is None or Slist is '':
                return
            self.lineSlist.setText(Slist)
            info_message = '''載入物種清單批次處理時，將會在同一目錄另存一個暫存檔(檔名_temp.txt/csv)，同時 \
並載入至下方的物種名錄清單中，您可修改後再產生名錄檔案。'''
            QMessageBox.information(self, "Info", info_message)
            Slist_str = str.split(Slist, '.')
            Slist_modified = Slist_str[0] + '_temp.' + Slist_str[1]
            self.lineTempFile.setText(Slist_modified)
            conn = sqlite3.connect('twnamelist.db')
            curs = conn.cursor()
            drop_table = '''DROP TABLE IF EXISTS sample;'''
            create_sample = '''CREATE TABLE sample (zh_name varchar);'''
            curs.execute(drop_table)
            curs.execute(create_sample)
            with codecs.open(Slist, 'r', 'utf-8') as f:
                reader = csv.reader(f, delimiter='|')
                for row in reader:
                    # substitute 台 to 臺
                    zhname = re.sub('台([灣|北|中|西|南|東])',r'臺\1', row[0])
                    insert_db = '''
                    INSERT INTO sample (zh_name) VALUES ("%s");
                    ''' % zhname
                    curs.execute(insert_db)
                conn.commit()
            f.close()
            # check the target database table
            db_table = self.checkDB()
            query_list = '''
            SELECT n.family_zh,n.name,n.zh_name FROM %s n, sample s
            WHERE n.zh_name = s.zh_name order by family,name;
            ''' % db_table
            curs.execute(query_list)
            fetched_results = curs.fetchall() 
            # clean the tree first
            self.delAllTreeItems() 
            for i in range(len(fetched_results)):
                item = QTreeWidgetItem()
                item.setText(0, fetched_results[i][0])
                item.setText(1, fetched_results[i][1])
                item.setText(2, fetched_results[i][2])
                self.treeWidget.addTopLevelItem(item)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 

    def browOutput(self):
        try:
            self.lineOutputFilename.clear()
            saveOutputFile = QFileDialog.getSaveFileName(self, self.tr("Save File as 儲存輸出的名錄檔案:"), \
                    QDir.homePath(), self.tr("Text files (*.docx *.odt *.txt)"))[0]
            if saveOutputFile is None or saveOutputFile is '':
                return
            self.lineOutputFilename.setText(saveOutputFile)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 

    # import data into auto-completion list
    def getCompleteData(self, model, blist):
        try:
            b_container = []
            with open(blist, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='|')
                for r in reader:
                    # only read common names, name without author and family common name
                    # ex: 松葉蕨, Psilotum nudum, 松葉蕨科
                    b_container.append(r[2] + "," + r[3] + "," + r[1])
            model.setStringList(b_container)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 

    def getDbIdx(self):
        try:
            g = genlist_api.Genlist()
            db_idx = self.comboDBselect.currentIndex()
            if db_idx == 0:
                # APG III
                retrieved = g.dbGetsp('dao_pnamelist_apg3')        
            elif db_idx == 1:
                # Flora of Taiwan
                retrieved = g.dbGetsp('dao_pnamelist')        
            elif db_idx == 2:
                # Birdlist of Taiwan
                retrieved = g.dbGetsp('dao_bnamelist')
            else:
                retrieved = g.dbGetsp('dao_pnamelist_apg3')        
            retrieved = DataFrame(retrieved)
            # returnlist
            return(retrieved)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))


    def addToTree(self):
        try:
            if self.lineSpecies.text() is '':
                QMessageBox.information(self, "Warning", "請輸入物種名稱!")
                return
            else:
                # check for species items
                item = QTreeWidgetItem()     
                species_item = str.split(str(self.lineSpecies.text()), ',')
                splist = self.getDbIdx()
                exists = 0
                for i, j in enumerate(list(splist[3])):
                    if j == species_item[0]:
                        exists = 1
                if exists == 1:
                   item.setText(0, species_item[2])
                   item.setText(1, species_item[1])
                   item.setText(2, species_item[0])
                   self.treeWidget.addTopLevelItem(item)
                   self.lineSpecies.clear()
                else:
                    QMessageBox.information(self, "Warning", "物種名稱%s不存在資料庫中!" % species_item[0])
                    self.lineSpecies.clear()
            self.lineSpecies.clear()
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))

    def delFromTree(self):
        #removing the QTreeItemWidget object
        try:
            self.treeWidget.takeTopLevelItem(treeWidget.indexOfTopLevelItem(self))
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 

    def getTreeItems(self, tree_widget):
        try:
            all_items = []
            root = tree_widget.invisibleRootItem()
            child_count = root.childCount()
            for i in range(child_count):
                item = root.child(i)
                all_items.append(item.text(2))
            return all_items
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 

    def delAllTreeItems(self):
    # TODO: 加入是否確定要全部刪除的確定
        self.treeWidget.clear()

    def delSelectedItems(self):
        root = self.treeWidget.invisibleRootItem()
        for item in self.treeWidget.selectedItems():
                (item.parent() or root).removeChild(item)

    def loadSelectedTable(self):
        try:
            g = genlist_api.Genlist()
            completer = QCompleter()
            self.lineSpecies.setCompleter(completer)
            model = QStringListModel()
            completer.setModel(model)
            db_table = self.checkDB()
            sp_data = g.dbGetsp(db_table)
            b_container=[]
            for i in range(len(sp_data)):
                b_container.append(sp_data[i][3] +  "," + sp_data[i][4] + "," + sp_data[i][2])
            model.setStringList(b_container)
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
 
    #
    def genNamelist(self):
        try:
            g = genlist_api.Genlist()
            tree_item = self.getTreeItems(self.treeWidget)
            # getdbtable
            db_table = self.checkDB()

            #if self.lineBlist.text() == '':
            #    QMessageBox.information(self, "Warning", "請指定物種資料檔案")
            if self.lineOutputFilename.text() == '':
                QMessageBox.information(self, "Warning", "請指定輸出檔案名稱")
            elif self.lineTempFile.text() == '' and self.lineSlist == '':
                QMessageBox.information(self, "Warning", "請指定要存物種清單之檔案")
            else:
                saved_list = str(self.lineTempFile.text())
                f = open(saved_list, 'w')
                for sp in tree_item:
                    f.write("%s\n" % sp)
                f.close()
                ofile = str(self.lineOutputFilename.text())
                output_flist = str.split(ofile, '.')
                # before generate namelist, clean up the sample table in sqlite db
                conn = sqlite3.connect('twnamelist.db')
                curs = conn.cursor()
                curs.execute('DROP TABLE IF EXISTS sample;')
                conn.commit()
                # export outputfile
                g.genEngine('twnamelist.db', db_table, saved_list, output_flist[1], output_flist[0])
                QMessageBox.information(self, "名錄產生器", "名錄已產生完畢")
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))

    def browTempfile(self):
        try:
            self.lineTempFile.clear()
            saveTempFile = QFileDialog.getSaveFileName(self, self.tr("Save File as 開啟物種清單檔案:"), QDir.homePath(), \
                    self.tr("Text files (*.txt *.csv)"))[0]
            if saveTempFile is None or saveTempFile is '':
                return
            self.lineTempFile.setText(saveTempFile) 
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))

    def genList(self):
        try:
            g = genlist_api.Genlist()
            #if self.lineBlist.text() == '':
            #    QMessageBox.information(self, "Warning", "請指定物種資料檔案")
            if self.lineSlist.text() == '':
                QMessageBox.information(self, "Warning", "請指定物種清單檔案")
            elif self.lineOutputFilename.text() == '':
                QMessageBox.information(self, "Warning", "請指定輸出檔案名稱")
            else:
                dbfile = str(self.lineBlist.text())
                sample_file = str(self.lineSlist.text())
                ofile = str(self.lineOutputFilename.text())
                output_flist = str.split(ofile, '.')
                g.generator(dbfile, sample_file, output_flist[1], output_flist[0])
                QMessageBox.information(self, "名錄產生器", "名錄已產生完畢")
        except BaseException as e:
            QMessageBox.information(self, "Warning", str(e))
