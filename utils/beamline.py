from cheetah.particles import ParticleBeam
from cheetah.accelerator import Drift, Quadrupole, Segment, Screen
import torch

def create_beamline(devices:dict, screen_name:str, **params):

    segment_list = []
    keys = sorted([key for key in devices.keys()])
    for key_num, key in enumerate(keys):
        if 'QUAD' in key:
            l_eff = devices[key].get('metadata',{}).get('l_eff', .01)
            madname = devices[key].get('madname', f'missing_quadname_{key_num}')
            # how can I interact with it then?
            quad = Quadrupole(name = key, k1 = torch.tensor(0.0), length= torch.tensor(l_eff))
            drift = Drift(name = f'drift_{key_num}',length= torch.tensor(1.0))
            segment_list.append(quad)
            segment_list.append(drift)
        elif screen_name in key:
            madname = devices[key].get('madname', f'missing_screen_{key_num}')
            screen =  Screen(name = key, resolution= (params.get('nrow', 600), params.get('ncol',800)), is_active=True )
    segment_list.append(screen)
    segment = Segment(elements = segment_list)
    print(segment.elements)
    return segment

#TODO: screen improvements
#TODO: Z order all elements correctly
#TODO: Set correct drift lengths
#TODO: improve defaults?
#TODO: setup multiarea beamline
#z_pos = devices[key].get('metadata',{}).get('sum_l_meters', 'bad value')