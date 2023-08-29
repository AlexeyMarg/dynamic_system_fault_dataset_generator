import sys
from urllib import response
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QComboBox, QGridLayout, \
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QDesktopWidget, QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, QCheckBox, QFileDialog
from PyQt5.QtCore import Qt
import numpy as np
from scipy.integrate import odeint
from random import uniform
import pandas as pd

import matplotlib.pyplot as plt
    
class app_window(QWidget):
    def __init__(self):
        super().__init__()
        self.table_data = {'Type': [],
                           'Form': [],
                           'N': [],
                           'Min t': [],
                           'Max t': [],
                           'Min length': [],
                           'Max length': [],
                           'Params': [],
                           'u type': [],
                           'u params': []} 
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Fault dataset generator for linear system')
        self.resize(1000, 400)
        self.center()
        
        self.init_boxes()
              
        self.plant_status = False
        self.show()
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def init_boxes(self):
        self.plant_group = QGroupBox('Model parameters')
        self.plant_group.setFixedWidth(700)
        self.init_plant_UI()
        self.plant_group.setLayout(self.plant_grid)
        self.v1_box = QVBoxLayout()
        self.v1_widget = QWidget()
        self.v1_widget.setLayout(self.v1_box)
        self.v1_widget.setFixedWidth(700)
        self.v1_box.addWidget(self.plant_group)
        
        self.noise_group = QGroupBox('Measurement noise')
        self.noise_group.setFixedWidth(700)
        self.init_noise_UI()
        self.noise_group.setLayout(self.noise_grid)
        self.v1_box.addWidget(self.noise_group)
        
        self.time_group = QGroupBox('Time settings')
        self.time_group.setFixedWidth(700)
        self.init_time_UI()
        self.time_group.setLayout(self.time_grid)
        self.v1_box.addWidget(self.time_group)
        
        self.fault_settings_group = QGroupBox('Fault settings')
        self.fault_settings_group.setFixedWidth(700)
        self.fault_settings_group.setFixedHeight(200)
        self.init_fault_settings_UI()
        self.fault_settings_group.setLayout(self.fault_settings_grid)
        self.v1_box.addWidget(self.fault_settings_group)
        
        self.control_settings_group = QGroupBox('Input settings')
        self.control_settings_group.setFixedWidth(700)
        self.init_control_UI()
        self.control_settings_group.setLayout(self.control_grid)
        self.v1_box.addWidget(self.control_settings_group)
        
        self.add_to_plan_btn = QPushButton('Add to plan', self)
        self.add_to_plan_btn.setEnabled(False)
        self.add_to_plan_btn.clicked.connect(self.clicked_add_to_plan)
        self.v1_box.addWidget(self.add_to_plan_btn)
        
        self.v2_box = QVBoxLayout()
        self.v2_widget = QWidget()
        self.v2_widget.setLayout(self.v2_box)
        self.v2_widget.setFixedWidth(600)
        self.table_group = QGroupBox('Table of experiments')
        self.init_table_ui()
        self.table_group.setLayout(self.table_grid)
        self.v2_box.addWidget(self.table_group)
        
        self.h1_box = QHBoxLayout()
        self.h1_box.addWidget(self.v1_widget) 
        self.h1_box.addWidget(self.v2_widget)   
        
        self.setLayout(self.h1_box)
       
            
    def clicked_add_to_plan(self):
        fault_type = self.fault_type_combo.currentText()
        form = self.fault_form_combo.currentText()
        
        flag = True
        try:
            N = int(self.N_runs_le.text())
        except:
            self.raise_error_message('Wrong number of experiments')
            flag = False
            
        if fault_type == 'None':
            min_start = 0
            max_start = 0
            fault_min_duration = 0
            fault_max_duration = 0
            parameters = ''
        else: # there is a fault, chrck time
            try:
                min_start = float(self.fault_min_start_le.text())
                if min_start < 0:
                    self.raise_error_message('Wrong min start time')
                    flag = False
            except:
                self.raise_error_message('Wrong min start time')
                flag = False
            
            try:
                max_start = float(self.fault_max_start_le.text())
                if max_start < min_start:
                    self.raise_error_message('Wrong max start time')
                    flag = False
            except:
                self.raise_error_message('Wrong max start time')
                flag = False
                
            try:
                fault_min_duration = float(self.fault_min_duration_le.text())
                if fault_min_duration < 0:
                    self.raise_error_message('Wrong min duration')
                    flag = False
            except:
                self.raise_error_message('Wrong min duration')
                flag = False
            
            try:
                fault_max_duration = float(self.fault_max_duration_le.text())
                if fault_max_duration < fault_min_duration:
                    self.raise_error_message('Wrong max start')
                    flag = False
            except:
                self.raise_error_message('Wrong max start')
                flag = False
            
            # check fault settings
            if self.fault_form_combo.currentText() == '' and self.fault_type_combo.currentText() != 'Component': 
                self.raise_error_message('Choose type of fault')
                flag = False
            elif self.fault_form_combo.currentText() == 'Stuck':
                if fault_type == 'Input':
                    try:
                        parameters = int(self.stuck_input_le.text())
                        if parameters > len(self.A) or parameters < 1:
                            flag = False
                    except:
                        self.raise_error_message('Wrong input number')
                        flag = False
                else:
                    try:
                        parameters = int(self.stuck_output_le.text())
                        if parameters > len(self.A) or parameters < 1:
                            flag = False
                    except:
                        self.raise_error_message('Wrong output number')
                        flag = False 
            elif self.fault_form_combo.currentText() == 'Multiplicative':
                if fault_type == 'Input':
                    try:
                        parameters = self.multiplicative_input_le.text().replace('[', '').replace(']', '').replace(' ', '').split(',')
                        parameters[0] = int(parameters[0])
                        parameters[1] = float(parameters[1])
                        parameters[2] = float(parameters[2])
                        if len(parameters) != 3 or parameters[0] < 1 or parameters[0] > len(self.A) or parameters[1]>parameters[2]:
                            self.raise_error_message('Wrong input number')
                            flag = False
                    except:
                        self.raise_error_message('Wrong input number')
                        flag = False
                else:
                    try:
                        parameters = self.multiplicative_output_le.text().replace('[', '').replace(']', '').replace(' ', '').split(',')
                        parameters[0] = int(parameters[0])
                        parameters[1] = float(parameters[1])
                        parameters[2] = float(parameters[2])
                        if len(parameters) != 3 or parameters[0] < 1 or parameters[0] > len(self.A) or parameters[1]>parameters[2]:
                            self.raise_error_message('Wrong output number')
                            flag = False
                    except:
                        self.raise_error_message('Wrong output number')
                        flag = False
            elif self.fault_form_combo.currentText() == 'Constant':
                if fault_type == 'Input':
                    try:
                        parameters = self.constant_input_le.text().replace('[', '').replace(']', '').replace(' ', '').split(',')
                        parameters[0] = int(parameters[0])
                        parameters[1] = float(parameters[1])
                        parameters[2] = float(parameters[1])
                        if len(parameters) != 3 or parameters[0] < 1 or parameters[0] > len(self.A) or parameters[1]>parameters[2]:
                            self.raise_error_message('Wrong input number')
                            flag = False
                    except:
                        self.raise_error_message('Wrong input number')
                        flag = False
                else:
                    try:
                        parameters = self.constant_output_le.text().replace('[', '').replace(']', '').replace(' ', '').split(',')
                        parameters[0] = int(parameters[0])
                        parameters[1] = float(parameters[1])
                        parameters[2] = float(parameters[2])
                        if len(parameters) != 3 or parameters[0] < 1 or parameters[0] > len(self.A) or parameters[1]>parameters[2]:
                            self.raise_error_message('Wrong output number')
                            flag = False
                    except:
                        self.raise_error_message('Wrong output number')
                        flag = False
            else: # Component fault
                parameters = {}
                try:
                    dA = eval(self.dA_le.text())
                    if len(dA['min']) != len(self.A) or len(dA['max']) != len(self.A) or\
                        len(dA['min'][0]) != len(self.A[0]) or len(dA['max'][0]) != len(self.A[0]):
                        self.raise_error_message('\u0394 A is incompatible with A')
                        flag = False
                    else:
                        parameters['dA'] = dA
                except:
                    self.raise_error_message('\u0394 A is incompatible with A')
                    flag = False                
                try:
                    dB = eval(self.dB_le.text())
                    if len(dB['min']) != len(self.B) or len(dB['max']) != len(self.B) or \
                        len(dB['min'][0]) != len(self.B[0]) or len(dB['max'][0]) != len(self.B[0]):
                        self.raise_error_message('\u0394 B is incompatible with B')
                        flag = False
                    else:
                        parameters['dB'] = dB
                except:
                    self.raise_error_message('\u0394 B is incompatible with B')
                    flag = False
                    
                try:
                    dC = eval(self.dС_le.text())
                    if len(dC['min']) != len(self.C) or len(dC['max']) != len(self.C) or \
                        len(dC['min'][0]) != len(self.C[0]) or len(dC['max'][0]) != len(self.C[0]):
                        self.raise_error_message('\u0394 C is incompatible with C')
                        flag = False
                    else:
                        parameters['dC'] = dC
                except:
                    self.raise_error_message('\u0394 C is incompatible with C')
                    flag = False
                    
                try:
                    dD = eval(self.dD_le.text())
                    if len(dD['min']) != len(self.D) or len(dD['max']) != len(self.D) or \
                        len(dD['min'][0]) != len(self.D[0]) or len(dD['max'][0]) != len(self.D[0]):
                        self.raise_error_message('\u0394 D is incompatible with C')
                        flag = False
                    else:
                        parameters['dD'] = dD
                except:
                    self.raise_error_message('\u0394 D is incompatible with D')
                    flag = False
        
        # check control
        
        u_type = self.control_type_combo.currentText()
                
        if u_type == 'Constant':
            try:
                u_params = self.str_to_matrix(self.control_const_value_le.text())
                if (len(u_params) != len(self.B[0])):
                    flag = False
                    self.raise_error_message('Input is incompatible with B')
                for param in u_params:
                    min_input = float(param[0])
                    max_input = float(param[1])
                    if len(param) !=2 or (min_input > max_input):
                        flag = False
                        self.raise_error_message('Input is incompatible with B')                    
            except:
                self.raise_error_message('Wrong input value')
                flag = False 
        else:
            try:
                u_params = self.str_to_matrix(self.control_sin_value_le.text())
                if (len(u_params) != len(self.B[0])):
                    self.raise_error_message('Input is incompatible with B')
                    flag = False
                for row in u_params:
                    if len(row) !=3:
                        self.raise_error_message('Input is incompatible with B')
                        flag = False  
                        break
            except:
                self.raise_error_message('Input is incompatible with B')
                flag = False  
        
        
        if flag == True:
            self.table_data['Type'].append(fault_type)
            self.table_data['Form'].append(form)
            self.table_data['N'].append(str(N))
            self.table_data['Min t'].append(str(min_start))  
            self.table_data['Max t'].append(str(max_start)) 
            self.table_data['Min length'].append(str(fault_min_duration))
            self.table_data['Max length'].append(str(fault_max_duration))
            self.table_data['Params'].append(str(parameters))
            self.table_data['u type'].append(str(u_type))
            self.table_data['u params'].append(str(u_params))
            
            rowPosition = self.table_tbl.rowCount() 
            self.table_tbl.insertRow(rowPosition)
            self.table_tbl.setItem(rowPosition , 0, QTableWidgetItem(str(self.table_data['Type'][-1])))
            self.table_tbl.setItem(rowPosition , 1, QTableWidgetItem(str(self.table_data['Form'][-1])))
            self.table_tbl.setItem(rowPosition , 2, QTableWidgetItem(str(self.table_data['N'][-1]))) 
            self.table_tbl.setItem(rowPosition , 3, QTableWidgetItem(str(self.table_data['Min t'][-1]))) 
            self.table_tbl.setItem(rowPosition , 4, QTableWidgetItem(str(self.table_data['Max t'][-1])))
            self.table_tbl.setItem(rowPosition , 5, QTableWidgetItem(str(self.table_data['Min length'][-1])))
            self.table_tbl.setItem(rowPosition , 6, QTableWidgetItem(str(self.table_data['Max length'][-1]))) 
            self.table_tbl.setItem(rowPosition , 7, QTableWidgetItem(str(self.table_data['Params'][-1])))
            self.table_tbl.setItem(rowPosition , 8, QTableWidgetItem(str(self.table_data['u type'][-1]))) 
            self.table_tbl.setItem(rowPosition , 9, QTableWidgetItem(str(self.table_data['u params'][-1])))     
            

    
    def str_to_matrix(self, s):
        s= s.replace(' ', '')
        s = s.split('],[')
        m = []
        for i in range(len(s)):
            s[i] = s[i].replace('[', '').replace(']', '')
            temp = list(s[i].split(','))
            temp2 = []
            for j in range(len(temp)):
                temp2.append(float(temp[j]))
            m.append(temp2)                
        return m
        
               
    def init_plant_UI(self):
        self.plant_grid = QGridLayout()
        self.plant_A_lbl = QLabel('A = ')
        self.plant_A_lbl.setFixedWidth(50)
        self.plant_A_lbl.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.plant_A_lbl, 0, 0)
        self.plant_A_le = QLineEdit('[[0, 1], [-1, -2]]')
        self.plant_A_le.setFixedWidth(400)
        self.plant_A_le.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.plant_A_le, 0, 1, 1, 4)
        
        self.plant_B_lbl = QLabel('B = ')
        self.plant_B_lbl.setAlignment(Qt.AlignTop)
        self.plant_B_lbl.setFixedWidth(50)
        self.plant_grid.addWidget(self.plant_B_lbl, 1, 0)
        self.plant_B_le = QLineEdit('[[1, 0.1], [0.1, 1]]')
        self.plant_B_le.setFixedWidth(400)
        self.plant_B_le.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.plant_B_le, 1, 1, 1, 4)
        
        self.plant_C_lbl = QLabel('C = ')
        self.plant_C_lbl.setAlignment(Qt.AlignTop)
        self.plant_C_lbl.setFixedWidth(50)
        self.plant_grid.addWidget(self.plant_C_lbl, 2, 0)
        self.plant_C_le = QLineEdit('[[1, 0], [0, 1]]')
        self.plant_C_le.setFixedWidth(400)
        self.plant_C_le.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.plant_C_le, 2, 1, 1, 4)
        
        self.plant_D_lbl = QLabel('D = ')
        self.plant_D_lbl.setAlignment(Qt.AlignTop)
        self.plant_D_lbl.setFixedWidth(50)
        self.plant_grid.addWidget(self.plant_D_lbl, 3, 0)
        self.plant_D_le = QLineEdit('[[0, 0], [0, 0]]')
        self.plant_D_le.setFixedWidth(400)
        self.plant_D_le.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.plant_D_le, 3, 1, 1, 4)
        
        self.initial_conditions_min_lbl = QLabel('Min x0 = ')
        self.initial_conditions_min_lbl.setFixedWidth(50)
        self.initial_conditions_min_lbl.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.initial_conditions_min_lbl, 4, 0)
        self.initial_conditions_min_le = QLineEdit('[[0], [0]]')
        self.initial_conditions_min_le.setFixedWidth(150)
        self.initial_conditions_min_le.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.initial_conditions_min_le, 4, 1)
        
        self.initial_conditions_max_lbl = QLabel('Max x0 = ')
        self.initial_conditions_max_lbl.setAlignment(Qt.AlignTop)
        self.initial_conditions_max_lbl.setFixedWidth(50)
        self.plant_grid.addWidget(self.initial_conditions_max_lbl, 4, 2, alignment=Qt.AlignRight)
        self.initial_conditions_max_le = QLineEdit('[[0], [0]]')
        self.initial_conditions_max_le.setFixedWidth(150)
        self.initial_conditions_max_le.setAlignment(Qt.AlignTop)
        self.plant_grid.addWidget(self.initial_conditions_max_le, 4, 3, alignment=Qt.AlignLeft)
        
        self.discrete_ckb = QCheckBox('Discrete plant')
        self.plant_grid.addWidget(self.discrete_ckb, 0, 4, alignment=Qt.AlignLeft)
        
        self.set_edit_plant_btn = QPushButton('Set', self)
        self.set_edit_plant_btn.setFixedWidth(50)
        self.set_edit_plant_btn.clicked.connect(self.clicked_parse_plant)
        self.plant_grid.addWidget(self.set_edit_plant_btn, 5, 0, alignment=Qt.AlignLeft)
        
    def init_noise_UI(self):
        self.noise_grid = QGridLayout()
        self.noise_lbl = QLabel('[[mu1, sigma1], ...\n [mu_N, sigma_N]]=')
        self.noise_lbl.setFixedWidth(70)
        self.noise_lbl.setAlignment(Qt.AlignLeft)
        self.noise_grid.addWidget(self.noise_lbl, 0, 0)
        
        self.noise_le = QLineEdit('[[0, 0.5], [0, 0.1]]')
        self.noise_le.setAlignment(Qt.AlignLeft)
        self.noise_le.setFixedWidth(300)
        self.noise_grid.addWidget(self.noise_le, 0, 1)
        
    def init_time_UI(self):
        self.time_grid = QGridLayout()
        self.time_grid.setHorizontalSpacing(10)
        self.modeling_time_lbl = QLabel('Modeling time, s')
        #self.modeling_time_lbl.setAlignment(Qt.AlignLeft)
        self.time_grid.addWidget(self.modeling_time_lbl, 0, 0, 1, 1)
        
        self.modeling_time_le = QLineEdit('10')
        #self.modeling_time_le.setAlignment(Qt.AlignLeft)
        self.modeling_time_le.setFixedWidth(50)
        self.time_grid.addWidget(self.modeling_time_le, 0, 1)
        
        self.sampling_time_lbl = QLabel('Sampling time, s')
        #self.modeling_time_lbl.setAlignment(Qt.AlignLeft)
        self.time_grid.addWidget(self.sampling_time_lbl, 0, 6, 1, 5)
        
        self.sampling_time_le = QLineEdit('0.1')
        #self.sampling_time_le.setAlignment(Qt.AlignLeft)
        self.sampling_time_le.setFixedWidth(50)
        self.time_grid.addWidget(self.sampling_time_le, 0, 11, 1, 16)
        
    def init_fault_settings_UI(self):
        self.fault_settings_grid = QGridLayout()
        self.fault_settings_grid.setHorizontalSpacing(10)
        
        self.fault_type_lbl = QLabel('Fault type')
        self.fault_settings_grid.addWidget(self.fault_type_lbl, 0, 0, alignment=Qt.AlignLeft)
        
        self.fault_type_combo = QComboBox()
        self.fault_type_combo.setFixedWidth(80)
        self.fault_type_combo.addItems(['None', 'Input', 'Output', 'Component'])
        self.fault_type_combo.currentIndexChanged.connect(self.combo_change_fault_type)
        self.fault_settings_grid.addWidget(self.fault_type_combo, 0, 1, alignment=Qt.AlignLeft)        
        
        self.fault_form_lbl = QLabel('Fault form')
        self.fault_settings_grid.addWidget(self.fault_form_lbl, 0, 2, alignment=Qt.AlignLeft)
        self.fault_form_combo = QComboBox()
        self.fault_form_combo.setFixedWidth(120)
        self.fault_form_combo.addItems(['','Stuck', 'Multiplicative', 'Constant'])
        self.fault_form_combo.currentIndexChanged.connect(self.combo_change_fault_form)
        self.fault_settings_grid.addWidget(self.fault_form_combo, 0, 3, 1, 2, alignment=Qt.AlignLeft)
        self.fault_form_combo.setEnabled(False)
        
        self.N_runs_lbl = QLabel('N runs')
        self.fault_settings_grid.addWidget(self.N_runs_lbl, 0, 6, alignment=Qt.AlignRight)
        self.N_runs_le = QLineEdit('1')
        self.N_runs_le.setFixedWidth(30)
        self.fault_settings_grid.addWidget(self.N_runs_le, 0, 7, alignment=Qt.AlignLeft)
            
        self.stuck_input_lbl = QLabel('Input number')
        self.stuck_input_lbl.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.stuck_input_lbl, 1, 0)
        self.stuck_input_lbl.setVisible(False)
        self.stuck_input_le = QLineEdit('1')
        self.stuck_input_le.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.stuck_input_le, 1, 1)
        self.stuck_input_le.setVisible(False)
        
        self.multiplicative_input_lbl = QLabel('[Input, min, max]')
        self.multiplicative_input_lbl.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.multiplicative_input_lbl, 1, 0)
        self.multiplicative_input_lbl.setVisible(False)
        self.multiplicative_input_le = QLineEdit('[1, 1.5, 3]')
        self.multiplicative_input_le.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.multiplicative_input_le, 1, 1)
        self.multiplicative_input_le.setVisible(False)
        
        self.constant_input_lbl = QLabel('[Input, min, max]')
        self.constant_input_lbl.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.constant_input_lbl, 1, 0)
        self.constant_input_lbl.setVisible(False)
        self.constant_input_le = QLineEdit('[1, 0.5, 2]')
        self.constant_input_le.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.constant_input_le, 1, 1)
        self.constant_input_le.setVisible(False)
        
        ##################################
        
        self.stuck_output_lbl = QLabel('Output number')
        self.stuck_output_lbl.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.stuck_output_lbl, 1, 0)
        self.stuck_output_lbl.setVisible(False)
        self.stuck_output_le = QLineEdit('1')
        self.stuck_output_le.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.stuck_output_le, 1, 1)
        self.stuck_output_le.setVisible(False)
        
        self.multiplicative_output_lbl = QLabel('[Output, min, max]')
        self.multiplicative_output_lbl.setFixedWidth(100)
        self.fault_settings_grid.addWidget(self.multiplicative_output_lbl, 1, 0)
        self.multiplicative_output_lbl.setVisible(False)
        self.multiplicative_output_le = QLineEdit('[1, 1.5, 3]')
        self.multiplicative_output_le.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.multiplicative_output_le, 1, 1)
        self.multiplicative_output_le.setVisible(False)
        
        self.constant_output_lbl = QLabel('[Output, min, max]')
        self.constant_output_lbl.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.constant_output_lbl, 1, 0)
        self.constant_output_lbl.setVisible(False)
        self.constant_output_le = QLineEdit('[1, 0.5, 2]')
        self.constant_output_le.setFixedWidth(80)
        self.fault_settings_grid.addWidget(self.constant_output_le, 1, 1)
        self.constant_output_le.setVisible(False)
        
        self.dA_lbl = QLabel('\u0394A {min:[], max:[]}')
        self.dA_lbl.setFixedWidth(120)
        self.fault_settings_grid.addWidget(self.dA_lbl, 1, 0)
        self.dA_lbl.setVisible(False)
        self.dA_le = QLineEdit('{\'min\':[[0, 0], [0, 0]], \'max\':[[0.5, 0], [0, 0.3]]}')
        self.dA_le.setFixedWidth(250)
        self.fault_settings_grid.addWidget(self.dA_le, 1, 1, 1, 2)
        self.dA_le.setVisible(False)
        
        self.dB_lbl = QLabel('\u0394B {min:[], max:[]}')
        self.dB_lbl.setFixedWidth(120)
        self.fault_settings_grid.addWidget(self.dB_lbl, 2, 0)
        self.dB_lbl.setVisible(False)
        self.dB_le = QLineEdit('{\'min\':[[0, 0], [0, 0]], \'max\':[[0.1, 0], [0.1, 0]]}')
        self.dB_le.setFixedWidth(250)
        self.fault_settings_grid.addWidget(self.dB_le, 2, 1, 1, 2)
        self.dB_le.setVisible(False)
        
        self.dС_lbl = QLabel('\u0394C {min:[], max:[]}')
        self.dС_lbl.setFixedWidth(120)
        self.fault_settings_grid.addWidget(self.dС_lbl, 3, 0)
        self.dС_lbl.setVisible(False)
        self.dС_le = QLineEdit('{\'min\':[[0, 0], [0, 0]], \'max\':[[0, 0], [0, 0]]}')
        self.dС_le.setFixedWidth(250)
        self.fault_settings_grid.addWidget(self.dС_le, 3, 1, 1, 2)
        self.dС_le.setVisible(False)
        
        self.dD_lbl = QLabel('\u0394D {min:[], max:[]}')
        self.dD_lbl.setFixedWidth(120)
        self.fault_settings_grid.addWidget(self.dD_lbl, 4, 0)
        self.dD_lbl.setVisible(False)
        self.dD_le = QLineEdit('{\'min\':[[0, 0], [0, 0]], \'max\':[[0, 0], [0, 0]]}')
        self.dD_le.setFixedWidth(250)
        self.fault_settings_grid.addWidget(self.dD_le, 4, 1, 1, 2)
        self.dD_le.setVisible(False)
        
        self.fault_min_start_lbl = QLabel('Min start time')
        self.fault_settings_grid.addWidget(self.fault_min_start_lbl, 5, 0)
        self.fault_min_start_lbl.setVisible(False)
        self.fault_min_start_le = QLineEdit('5')
        self.fault_min_start_le.setFixedWidth(80)
        self.fault_min_start_le.setVisible(False)
        self.fault_settings_grid.addWidget(self.fault_min_start_le, 5, 1)
        
        self.fault_max_start_lbl = QLabel('Max start time')
        self.fault_settings_grid.addWidget(self.fault_max_start_lbl, 5, 2)
        self.fault_max_start_lbl.setVisible(False)
        self.fault_max_start_le = QLineEdit('8')
        self.fault_max_start_le.setFixedWidth(80)
        self.fault_max_start_le.setVisible(False)
        self.fault_settings_grid.addWidget(self.fault_max_start_le, 5, 3)
        
        self.fault_min_duration_lbl = QLabel('Min duration')
        self.fault_settings_grid.addWidget(self.fault_min_duration_lbl, 5, 4)
        self.fault_min_duration_lbl.setVisible(False)
        self.fault_min_duration_le = QLineEdit('2')
        self.fault_min_duration_le.setFixedWidth(80)
        self.fault_min_duration_le.setVisible(False)
        self.fault_settings_grid.addWidget(self.fault_min_duration_le, 5, 5)
        
        self.fault_max_duration_lbl = QLabel('Max duration')
        self.fault_settings_grid.addWidget(self.fault_max_duration_lbl, 5, 6)
        self.fault_max_duration_lbl.setVisible(False)
        self.fault_max_duration_le = QLineEdit('10')
        self.fault_max_duration_le.setFixedWidth(80)
        self.fault_max_duration_le.setVisible(False)
        self.fault_settings_grid.addWidget(self.fault_max_duration_le, 5, 7)
        
    def init_control_UI(self):
        self.control_grid = QGridLayout()
        self.control_grid.setHorizontalSpacing(10)
        
        self.control_form_lbl = QLabel('Form')
        self.control_form_lbl.resize(self.control_form_lbl.sizeHint())
        self.control_grid.addWidget(self.control_form_lbl, 0, 0, alignment=Qt.AlignRight)
        
        self.control_type_combo = QComboBox()
        self.control_type_combo.resize(self.control_type_combo.sizeHint())
        self.control_type_combo.addItems(['Constant', 'Sin wave'])
        self.control_type_combo.currentIndexChanged.connect(self.combo_change_control_type)
        self.control_grid.addWidget(self.control_type_combo, 0, 1, alignment=Qt.AlignLeft)
        
        self.control_const_value_lbl = QLabel('[[min, max], ...]')
        self.control_const_value_lbl.resize(self.control_const_value_lbl.sizeHint())
        self.control_grid.addWidget(self.control_const_value_lbl, 0, 2, alignment=Qt.AlignRight)
        
        self.control_const_value_le = QLineEdit('[[-0.5, 0.5], [0, 0]]')
        self.control_const_value_le.setFixedWidth(150)
        self.control_grid.addWidget(self.control_const_value_le, 0, 3, alignment=Qt.AlignLeft)
        
        self.control_sin_value_lbl = QLabel('[[max_amp, max_w, max_phase], ...]')
        self.control_sin_value_lbl.resize(self.control_sin_value_lbl.sizeHint())
        self.control_sin_value_lbl.setVisible(False)
        self.control_grid.addWidget(self.control_sin_value_lbl, 0, 2, alignment=Qt.AlignRight)
        
        self.control_sin_value_le = QLineEdit('[[20, 10, 6], [0, 0, 0]]')
        self.control_sin_value_le.setFixedWidth(150)
        self.control_sin_value_le.setVisible(False)
        self.control_grid.addWidget(self.control_sin_value_le, 0, 3, alignment=Qt.AlignLeft)
    
    def init_table_ui(self):
        self.table_grid = QGridLayout()
        self.table_grid.setHorizontalSpacing(10)
        
        self.table_tbl = QTableWidget()
        self.table_tbl.setEnabled(False)
        headers = self.table_data.keys()
        self.table_tbl.setColumnCount(len(headers))
        self.table_tbl.setHorizontalHeaderLabels(headers)
        self.table_tbl.setColumnWidth(0, 40)
        self.table_tbl.setColumnWidth(1, 40)
        self.table_tbl.setColumnWidth(2, 20)
        self.table_tbl.setColumnWidth(3, 40)
        self.table_tbl.setColumnWidth(4, 40)
        self.table_tbl.setColumnWidth(5, 70)
        self.table_tbl.setColumnWidth(6, 80)
        self.table_tbl.setColumnWidth(7, 80)
        self.table_tbl.setColumnWidth(8, 50)
        self.table_tbl.setColumnWidth(9, 80)
        self.table_grid.addWidget(self.table_tbl, 0, 0)
        
        self.table_enable_ckb = QCheckBox('Edit table', self)
        self.table_enable_ckb.stateChanged.connect(self.checked_table_enable)
        self.table_grid.addWidget(self.table_enable_ckb, 1, 0)
        
        self.generate_btn = QPushButton('Generate', self)
        self.generate_btn.clicked.connect(self.clicked_generate)
        self.table_grid.addWidget(self.generate_btn, 2, 0)
    
    def combo_change_control_type(self):
        if self.control_type_combo.currentText() == 'Constant':
            self.control_const_value_lbl.setVisible(True)
            self.control_const_value_le.setVisible(True)
            self.control_sin_value_lbl.setVisible(False)
            self.control_sin_value_le.setVisible(False)
        else:
            self.control_const_value_lbl.setVisible(False)
            self.control_const_value_le.setVisible(False)
            self.control_sin_value_lbl.setVisible(True)
            self.control_sin_value_le.setVisible(True)
        
    def checked_table_enable(self):
        if self.table_enable_ckb.isChecked() == True:
            self.table_tbl.setEnabled(True)
        else:
            self.table_tbl.setEnabled(False)
    
    def combo_change_fault_type(self):
        self.hide_time_fault_settings()
        self.hide_form_fault_settings()
        if self.fault_type_combo.currentText() == 'None':
            self.fault_form_combo.setEnabled(False)
        elif self.fault_type_combo.currentText() == 'Component':
            self.fault_form_combo.setEnabled(False)
            self.show_fault_time_settings()
        else:
            self.show_fault_time_settings()
            self.fault_form_combo.setEnabled(True)
        self.fault_form_combo.setCurrentIndex(1)  
        self.fault_form_combo.setCurrentIndex(0) 
        
    
    
            
    def combo_change_fault_form(self):
        self.hide_form_fault_settings() 
        if self.fault_form_combo.currentText() == '':
            if self.fault_type_combo.currentText() == 'Component':
                self.dA_lbl.setVisible(True)
                self.dA_le.setVisible(True)
                self.dB_lbl.setVisible(True)
                self.dB_le.setVisible(True)
                self.dС_lbl.setVisible(True)
                self.dС_le.setVisible(True)
                self.dD_lbl.setVisible(True)
                self.dD_le.setVisible(True) 
        if self.fault_form_combo.currentText() == 'Stuck':
            if self.fault_type_combo.currentText() == 'Input':
                self.stuck_input_lbl.setVisible(True)
                self.stuck_input_le.setVisible(True)
            else:
                self.stuck_output_lbl.setVisible(True)
                self.stuck_output_le.setVisible(True)
        elif self.fault_form_combo.currentText() == 'Multiplicative':
            if self.fault_type_combo.currentText() == 'Input':
                self.multiplicative_input_lbl.setVisible(True)
                self.multiplicative_input_le.setVisible(True)
            else:
                self.multiplicative_output_lbl.setVisible(True)
                self.multiplicative_output_le.setVisible(True)
        elif self.fault_form_combo.currentText() == 'Constant':
            if self.fault_type_combo.currentText() == 'Input':
                self.constant_input_lbl.setVisible(True)
                self.constant_input_le.setVisible(True)
            else:
                self.constant_output_lbl.setVisible(True)
                self.constant_output_le.setVisible(True)
               
    
    def hide_time_fault_settings(self):
        self.fault_min_start_lbl.setVisible(False)
        self.fault_min_start_le.setVisible(False)
        self.fault_max_start_lbl.setVisible(False)
        self.fault_max_start_le.setVisible(False)
            
        self.fault_min_duration_lbl.setVisible(False)
        self.fault_min_duration_le.setVisible(False)
        self.fault_max_duration_lbl.setVisible(False)
        self.fault_max_duration_le.setVisible(False)
                    
    def hide_form_fault_settings(self):        
        self.stuck_input_lbl.setVisible(False)
        self.stuck_input_le.setVisible(False)
        self.multiplicative_input_lbl.setVisible(False)
        self.multiplicative_input_le.setVisible(False)
        self.constant_input_lbl.setVisible(False)
        self.constant_input_le.setVisible(False) 
        self.stuck_output_lbl.setVisible(False)
        self.stuck_output_le.setVisible(False)
        self.multiplicative_output_lbl.setVisible(False)
        self.multiplicative_output_le.setVisible(False)
        self.constant_output_lbl.setVisible(False)
        self.constant_output_le.setVisible(False)
        
        self.dA_lbl.setVisible(False)
        self.dA_le.setVisible(False)
        self.dB_lbl.setVisible(False)
        self.dB_le.setVisible(False)
        self.dС_lbl.setVisible(False)
        self.dС_le.setVisible(False)
        self.dD_lbl.setVisible(False)
        self.dD_le.setVisible(False) 
        
    def show_fault_time_settings(self):
        self.fault_min_start_lbl.setVisible(True)
        self.fault_min_start_le.setVisible(True)
        self.fault_max_start_lbl.setVisible(True)
        self.fault_max_start_le.setVisible(True)
            
        self.fault_min_duration_lbl.setVisible(True)
        self.fault_min_duration_le.setVisible(True)
        self.fault_max_duration_lbl.setVisible(True)
        self.fault_max_duration_le.setVisible(True)
        
    
   
    def raise_error_message(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")
        msg.exec_()
        
    def clicked_parse_plant(self):
        if self.plant_status == False:
            flag = True
            try:
                self.A =  np.array(self.str_to_matrix(self.plant_A_le.text()))
            except:
                self.raise_error_message('Unable to parse matrix A')
                flag = False
                
            try:
                self.B =  np.array(self.str_to_matrix(self.plant_B_le.text()))
            except:
                self.raise_error_message('Unable to parse matrix B')
                flag = False            
            try:
                self.C =  np.array(self.str_to_matrix(self.plant_C_le.text()))
            except:
                self.raise_error_message('Unable to parse matrix C')
                flag = False  
                
            try:
                self.D =  np.array(self.str_to_matrix(self.plant_D_le.text()))
            except:
                self.raise_error_message('Unable to parse matrix D')
                flag = False
                
            try:
                self.x0_min = np.array(self.str_to_matrix(self.initial_conditions_min_le.text())) 
            except:
                self.raise_error_message('Unable to parse min x0')
                flag = False
                
            try:
                self.x0_max = np.array(self.str_to_matrix(self.initial_conditions_max_le.text())) 
            except:
                self.raise_error_message('Unable to parse max x0')
                flag = False
                
            try:
                self.noise = np.array(self.str_to_matrix(self.noise_le.text())) 
            except:
                self.raise_error_message('Unable to parse noise')
                flag = False
                
            try:
                self.modeling_time = float(self.modeling_time_le.text())
                if  self.modeling_time<0:
                    self.raise_error_message('Wrong modeling time')
                    flag = False
            except:
                self.raise_error_message('Wrong modeling time')
                flag = False
                
            try:
                self.sampling_time = float(self.sampling_time_le.text())
                if  self.sampling_time<0 or self.sampling_time >= self.modeling_time:
                    self.raise_error_message('Wrong sampling time')
                    flag = False
            except:
                self.raise_error_message('Wrong sampling time')
                flag = False
                
                
            if flag == True:
                flag = self.check_plant_consistence()
                
        
            self.plant_status = flag
            if self.plant_status == True:
                self.set_edit_plant_btn.setText('Edit')
                print(f'A = {self.A}\n B = {self.B}\nC = {self.C}\nD = {self.D}\nx0_min = {self.x0_min}\nx0_max = {self.x0_max}')
                self.plant_A_le.setEnabled(False)
                self.plant_B_le.setEnabled(False) 
                self.plant_C_le.setEnabled(False) 
                self.plant_D_le.setEnabled(False) 
                self.initial_conditions_min_le.setEnabled(False) 
                self.initial_conditions_max_le.setEnabled(False) 
                self.noise_le.setEnabled(False)
                self.modeling_time_le.setEnabled(False)
                self.sampling_time_le.setEnabled(False)
                self.discrete_ckb.setEnabled(False)
                self.add_to_plan_btn.setEnabled(True)
                  
                
        else:
            self.plant_status = False
            self.set_edit_plant_btn.setText('Set')
            self.plant_A_le.setEnabled(True)
            self.plant_B_le.setEnabled(True) 
            self.plant_C_le.setEnabled(True) 
            self.plant_D_le.setEnabled(True) 
            self.initial_conditions_min_le.setEnabled(True) 
            self.initial_conditions_max_le.setEnabled(True)
            self.noise_le.setEnabled(True)
            self.modeling_time_le.setEnabled(True)
            self.sampling_time_le.setEnabled(True)
            self.discrete_ckb.setEnabled(True)
            self.add_to_plan_btn.setEnabled(False)
            self.clear_table()
            
    
    def clear_table(self):
        self.table_data = {'Type': [],
                           'Form': [],
                           'N': [],
                           'Min t': [],
                           'Max t': [],
                           'Min length': [],
                           'Max length': [],
                           'Params': [],
                           'u type': [],
                           'u params': []}
        self.table_tbl.setRowCount(0)
                
        
    def check_plant_consistence(self):
        if len(self.A) != len(self.A[0]):
            self.raise_error_message('A is not square')
            return False
        else:
            order = len(self.A)
            print(order)
            
        if len(self.B) != order:
            self.raise_error_message('A and B are incompatible')
            return False
        else:
            B_cols = len(self.B[0]) 
            
        if len(self.C[0]) != order:
            self.raise_error_message('A and C are incompatible')
            return False
        else:
            C_rows = len(self.C)
            
        if len(self.D) != C_rows or len(self.D[0]) != B_cols:
            self.raise_error_message('B, C and D are incompatible')
            return False
        
        if len(self.x0_min) != order or len(self.x0_max)!= order:
            self.raise_error_message('Wrong x0 order')
            return False
        
        if len(self.noise[0]) != 2 or len(self.noise) != C_rows:
            self.raise_error_message('Wrong noise data')
            return False
        
        for i in range(len(self.x0_min)):
            if self.x0_min[i] > self.x0_max[i]:
                self.raise_error_message('Max x0 shoulf be greater than min x0')
                return False
            
        return True
        


    def clicked_generate(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        N_experiment = 0
        
        
        time = np.arange(0, self.modeling_time, self.sampling_time)
            
         
        for i in range(self.table_tbl.rowCount()):
            fault_type = self.table_tbl.item(i, 0).text()
            fault_form = self.table_tbl.item(i, 1).text()
            fault_N = int(self.table_tbl.item(i, 2).text())
            fault_min_start = float(self.table_tbl.item(i, 3).text())
            fault_max_start = float(self.table_tbl.item(i, 4).text())
            fault_min_duration = float(self.table_tbl.item(i, 5).text())
            fault_max_duration = float(self.table_tbl.item(i, 6).text())
            fault_params = self.table_tbl.item(i, 7).text()
            if fault_params != '':
                fault_params = eval(fault_params)
            u_type = self.table_tbl.item(i, 8).text()
            u_params = np.array(self.str_to_matrix(self.table_tbl.item(i, 9).text()))
            u_params2 = u_params.copy()
            
            if fault_type == 'Component':
                dA_min = fault_params['dA']['min']
                dA_max = fault_params['dA']['max']
                self.dA = np.zeros((len(self.A), len(self.A[0])))
                for row in range(len(self.A)):
                    for col in range(len(self.A[0])):
                        self.dA[row, col] = uniform(float(dA_min[row][col]), float(dA_max[row][col]))
                dB_min = fault_params['dB']['min']
                dB_max = fault_params['dB']['max']
                self.dB = np.zeros((len(self.B), len(self.B[0])))
                for row in range(len(self.B)):
                    for col in range(len(self.B[0])):
                        self.dB[row, col] = uniform(float(dB_min[row][col]), float(dB_max[row][col]))
                dC_min = fault_params['dC']['min']
                dC_max = fault_params['dC']['max']
                self.dC = np.zeros((len(self.C), len(self.C[0])))
                for row in range(len(self.C)):
                    for col in range(len(self.C[0])):
                        self.dC[row, col] = uniform(float(dC_min[row][col]), float(dC_max[row][col]))
                dD_min = fault_params['dD']['min']
                dD_max = fault_params['dD']['max']
                self.dD = np.zeros((len(self.D), len(self.D[0])))
                for row in range(len(self.D)):
                    for col in range(len(self.D[0])):
                        self.dD[row, col] = uniform(float(dD_min[row][col]), float(dD_max[row][col]))
                        
                        

            for j in range(fault_N):
                u_params = u_params2.copy()
                N_experiment += 1

                x0 = []
                for i in range(len(self.x0_min)):
                    x0.append([uniform(self.x0_min[i][0], self.x0_max[i][0])])
                x0 = np.array(x0)
                
                fault_start = uniform(fault_min_start, fault_max_start)
                fault_stop = fault_start + uniform(fault_min_duration, fault_max_duration)

                
                # u precalculation
                u_history = np.zeros((len(self.B[0]), len(time)))
                u_faults_history = np.zeros((len(self.B[0]), len(time)))
                
                if u_type == 'Constant':
                    u_value = np.zeros((len(self.B[0]), 1))
                    for i, param in enumerate(u_params):
                        u_value[i][0] = np.random.uniform(param[0], param[1])
                    u_params = u_value
                else:
                    u_value = np.zeros((len(self.B[0]), 3))
                    for i, param in enumerate(u_params):
                        u_value[i][0] = np.random.uniform(0, param[0])
                        u_value[i][1] = np.random.uniform(0, param[1])
                        u_value[i][2] = np.random.uniform(0, param[2])
                    u_params = u_value
                        
                
                
                # input faults
                for step in range(len(time)):
                    if u_type == 'Constant':
                        u_history[:, step] = u_params.ravel()
                    else:
                        u_history[:, step] = (u_params[:, 0] * np.sin(u_params[:, 1]*time[step] + u_params[:, 2])).ravel()
                    
                if fault_type == 'Input':
                    if fault_form == 'Stuck':
                        if u_type == 'Sin wave':
                            N_input = fault_params - 1
                            u_stuck = u_params[N_input, 0] * np.sin(u_params[N_input, 1]*fault_start + u_params[N_input, 2])
                            for step, t in enumerate(time):
                                if fault_start<t<fault_stop:
                                    u_history[N_input, step] = u_stuck.ravel()
                                    u_faults_history[N_input, step] = 1
                    elif fault_form == 'Multiplicative':
                        N_input, value = fault_params[0] - 1, uniform(fault_params[1], fault_params[2]) 
                        for step, t in enumerate(time):
                                if fault_start<t<fault_stop:
                                    u_history[N_input, step] = value* float(u_history[N_input, step])
                                    u_faults_history[N_input, step] = 2
                    else: #constant
                       N_input, value = fault_params[0] - 1, uniform(fault_params[1], fault_params[2]) 
                       for step, t in enumerate(time):
                                if fault_start<t<fault_stop:
                                    u_history[N_input, step] = value
                                    u_faults_history[N_input, step] = 3                                     

                # state history calculation
                fault_status_history = np.zeros(time.shape)
                for step, t in enumerate(time):
                    if fault_start<t<fault_stop:
                        fault_status_history[step] = 1
                
                if self.discrete_ckb.isChecked() == False:
                    state_history = odeint(self.model_func, x0.ravel(), time, args=(time, fault_status_history, fault_type, u_history))
                    print('\n\n\n Shape ', state_history.shape)
                    state_history = state_history.reshape(state_history.shape[1], -1)
                else:
                    state_history = self.calc_discrete_state_history(x0, time, fault_start, fault_stop, fault_type, u_history)
                
                
                # output precalculation
                y_history = np.zeros((len(self.C), len(time)))
                y_nominal = np.zeros((len(self.C), len(time)))
                y_faults_history = np.zeros((len(self.C), len(time)))
                comp_faults_history = np.zeros((1, len(time)))
                for step in range(len(time)):
                    x = state_history[:, step].reshape(-1, 1)
                    u = u_history[:, step].reshape(-1, 1)
                    xi = np.zeros((len(self.C), 1))
                    for row, data in enumerate(self.noise):
                        xi[row, 0] = np.random.normal(loc=data[0], scale=data[1])
                    y_history[:, step] = (np.matmul(self.C, x) + np.matmul(self.D, u) + xi).ravel()
                    y_nominal[:, step] = np.matmul(self.C, x).ravel()
                    #print('Nominal shape: ', y_nominal.shape)
                # output faults
                if fault_type == 'Output':
                    if fault_form == 'Stuck':
                        N_output = int(fault_params) - 1
                        step_start = int(fault_start // self.sampling_time)
                        step_stop = int(fault_stop // self.sampling_time)
                        y_stuck = y_history[N_output, step_start]
                        for step, t in enumerate(time):
                            if fault_start<t<fault_stop:
                                y_history[N_output, step] = y_stuck
                                y_faults_history[N_output, step] = 1
                    elif fault_form == 'Multiplicative':
                        N_output = int(fault_params[0]) - 1
                        value = uniform(fault_params[1], fault_params[2])
                        for step, t in enumerate(time):
                            if fault_start<t<fault_stop:
                                y_history[N_output, step] = value * y_history[N_output, step]
                                y_faults_history[N_output, step] = 2
                    else: #constant
                        N_output = int(fault_params[0]) - 1
                        value = uniform(fault_params[1], fault_params[2])
                        for step, t in enumerate(time):
                            if fault_start<t<fault_stop:
                                y_history[N_output, step] = value
                                y_faults_history[N_output, step] = 3
                                
                # component faults
                if fault_type == 'Component':
                    step_start = int(fault_start // self.sampling_time)
                    step_stop = int(fault_stop // self.sampling_time)
                    for step in range(len(time)):
                        if step_start<step<step_stop:
                            x = state_history[:, step].reshape(-1, 1)
                            u = u_history[:, step].reshape(-1, 1)
                            y_history[:, step] += (np.matmul(self.dC, x) + np.matmul(self.dD, u) + xi).ravel()
                    comp_faults_history[0, step_start:step_stop] = 1
                                
                
                u_cols, y_cols, y_nom_cols, u_f_cols, y_f_cols, comp_cols  = \
                    u_history.T, y_history.T, y_nominal.T, u_faults_history.T, y_faults_history.T, comp_faults_history.T
                dataset = np.c_[u_cols, y_cols, y_nom_cols, u_f_cols, y_f_cols, comp_cols]
                
                headers = []
                for i in range(len(self.B[0])):
                    headers.append('u'+str(i+1))
                for i in range(len(self.C)):
                    headers.append('y'+str(i+1))
                for i in range(len(self.C)):
                    headers.append('y_nominal'+str(i+1))    
                for i in range(len(self.B[0])):
                    headers.append('fault_u'+str(i+1))
                for i in range(len(self.C)):
                    headers.append('fault_y'+str(i+1))
                headers.append('comp_fault')
                           
                file_name = folder + '/experiment' + str(N_experiment) + '.csv'
                                
                pd.DataFrame(dataset, columns=headers).to_csv(file_name)
                
  
    def calc_discrete_state_history(self, x0, time, fault_start, fault_stop, fault_type, u_history):
        state_history = np.zeros((len(x0), len(time)))
        x = x0
        state_history[:, 0] = x.ravel()
        if fault_type != 'Component':
            for step in range(u_history.shape[1]):
                u_row = u_history[:, step].ravel()
                x = np.matmul(self.A, x.reshape(-1, 1)) + np.matmul(self.B, u_row).reshape(-1, 1)
                state_history[:, step] = x.ravel()
        else:
            for step in range(u_history.shape[1]):
                u_row = u_history[:, step].ravel()
                if fault_start<time[step]<fault_stop:
                    fault_status = 1
                else:
                    fault_status = 0
                x = np.matmul(self.A + fault_status * self.dA, x.reshape(-1, 1)) + np.matmul(self.B + fault_status * self.dB, u_row).reshape(-1, 1)
                state_history[:, step] = x.ravel()
        return state_history
        
    
    def model_func(self, x, t, time, fault_status_history,  fault_type, u_history):
        if fault_type != 'Component':
            u = np.zeros((len(u_history), 1))
            for row in range(len(u_history)):
                u_row = u_history[row, :].ravel()
                u_applied = np.interp(t, time, u_row)
                u[row, 0] = u_applied
            dxdt = np.matmul(self.A, x.reshape(-1, 1)) + np.matmul(self.B, u)
        else:
            u = np.zeros((len(u_history), 1))
            for row in range(len(u_history)):
                u_row = u_history[row, :].ravel()
                u_applied = np.interp(t, time, u_row)
                u[row, 0] = u_applied
                fault_status = np.interp(t, time, fault_status_history)
            dxdt = np.matmul(self.A + fault_status * self.dA, x.reshape(-1, 1)) + np.matmul(self.B + fault_status * self.dB, u)
        return dxdt.ravel()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = app_window()
    sys.exit(app.exec_())