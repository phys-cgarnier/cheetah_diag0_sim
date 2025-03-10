from pcaspy import Driver
from cheetah.particles import ParticleBeam
from cheetah.accelerator import Segment
import numpy as np
import torch
from lcls_tools.common.data.model_general_calcs import bdes_to_kmod, kmod_to_bdes
import threading
from concurrent.futures import ThreadPoolExecutor
import time
class SimDriver(Driver):
    def __init__(self, particle_beam: ParticleBeam, beamline: Segment, screen: str, devices: dict):
        super().__init__()
        self.devices = devices
        self.sim_beam = particle_beam
        self.sim_beamline = beamline
        self.image_data = np.array([])
        self.screen = screen
        
        self.set_defaults_for_ctrl(0)
        self.sim_beamline.transfer_maps_merged(self.sim_beam)
        self.otr2_image = self.sim_beamline.otr2.reading.flatten().tolist()



    def set_defaults_for_ctrl(self,default_value:int):
        for key in list(self.devices.keys()):
            if 'QUAD' in key:
                ctrl_pv = key+":CTRL"
                self.setParam(ctrl_pv,default_value)

    def get_bact_defaults(self): 
        
        names = [element.name for element in self.sim_beamline.elements]
        for key in list(self.devices.keys()):
            if 'QUAD' in key and 'BACT' in key:
                madname = self.devices[key]["madname"]

    def read(self,reason):
        if 'Image:ArrayData' in reason and reason.rsplit(':',2)[0] == self.screen:
            print('reading screen')
            madname = self.devices[self.screen]["madname"]
            self.image_data = self.get_screen_distribution(screen_name = madname)
            value = self.image_data.flatten().tolist()
        elif 'QUAD' in reason and 'BCTRL' in reason:
            quad_name = reason.rsplit(':',1)[0]
            madname = self.devices[quad_name]["madname"]
            value = self.get_quad_value(madname)
        elif 'QUAD' in reason and 'BACT' in reason:
            quad_name = reason.rsplit(':',1)[0]
            madname = self.devices[quad_name]["madname"]
            value = self.get_quad_value(madname)
        else:
            value = self.getParam(reason)
        return value

    def write(self, reason, value):
        if 'QUAD' in reason and 'BCTRL' in reason:
            quad_name = reason.rsplit(':',1)[0]
            madname = self.devices[quad_name]["madname"]
            self.set_quad_value(madname,value)
        elif 'QUAD' in reason and 'BACT' in reason:
            pass
        elif 'QUAD' in reason:
            self.setParam(reason,value)
        elif 'OTRS' in reason:
            print(f"""Write to OTRS pvs is disabled, 
                  failed to write to {reason}""")

    
    def get_quad_value(self, quad_name:str):
        names = [element.name for element in self.sim_beamline.elements]
        if quad_name in names:
            index_num = names.index(quad_name)
            kmod = self.sim_beamline.elements[index_num].k1.item()
            length = self.sim_beamline.elements[index_num].length.item()
            energy = self.sim_beam.energy.item()
            quad_value = kmod_to_bdes(e_tot= energy, effective_length = length, k = kmod)
            
            #quad_value =self.sim_beamline.elements[index_num].k1.item()
            print(f"kmod is {kmod} with quad_value {quad_value}")
        else:
            print(f"""Warning {quad_name} not in Segment""")
            quad_value = np.nan
        return quad_value

    def set_quad_value(self, quad_name:str, quad_value:float):
        ''' Takes quad ctrl name and the k1 strength if the quad is in beamline'''
        names = [element.name for element in self.sim_beamline.elements]
        if quad_name in names:
            index_num = names.index(quad_name)
            length = (self.sim_beamline.elements[index_num].length).item()
            energy = self.sim_beam.energy.item()
            kmod = bdes_to_kmod(e_tot=energy, effective_length=length, bdes = quad_value)

            self.sim_beamline.elements[index_num].k1 = torch.tensor(kmod)
            print(f"""Quad in segment with name {quad_name}
                   set to kmod {kmod} with quad value {quad_value}""")

    def get_screen_distribution(self, screen_name:str)->list[float]:
        #TODO: put some safety stuff in here
        self.sim_beamline.track(self.sim_beam)

        names = [element.name for element in self.sim_beamline.elements]
        if screen_name in names:
            index_num = names.index(screen_name)
            img = self.sim_beamline.elements[index_num].reading
            return img
        
#TODO: start server takebeam size measurements and plot them in experiment.nb - image isn't processing
#TODO: build cheetah accelerator with madname instead of control name -> done I think? 
#TODO: when a bctrl or image pv is called look up the pv in the accelerator by madname

#TODO: build in wait_time when performing scans
#TODO: when caput to bctrl -> set bact pv,