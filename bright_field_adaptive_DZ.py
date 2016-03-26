#developed by Dianmu Zhang
#updated March 2016
#system requirement: python 2.7, python package: numpy, scipy, skimage, matplotlib
#this is a script automatically identfies and characterizes yeast cells from bright field microscopic images
#characterizations features: area, orientation, (centroid coordinate)

#import sys
#sys.path.append('C:/Users/Dianmu Zhang/Documents/Python Scripts')
import numpy as np
from scipy import ndimage as ndi
import matplotlib.pyplot as plt

from skimage.filters import sobel
from skimage.segmentation import slic, join_segmentations
from skimage.morphology import watershed
from skimage.color import label2rgb
from skimage import data, img_as_float
import skimage.morphology
from skimage.morphology import disk,square,diamond
from skimage.segmentation import find_boundaries
from skimage import measure
from skimage.filters import threshold_otsu, threshold_adaptive

import numpy as np
import skimage
import skimage.io
import os, sys

#Customerization field, change as needed
#file handling
#import os, sys

picpath= 'C:/Users/Dianmu Zhang/OneDrive/Documents/UW work/paper/project related/image processing/sample pictures'
savepath='C:/Users/Dianmu Zhang/OneDrive/Documents/UW work/paper/project related/image processing/sample pictures/results'
filelist= os.listdir(picpath)

def image_processing(picname, picpath, savepath):
	#image processing part
	#get threshold from cummulative historgram
    #filename='pic1.jpg'
	os.chdir(picpath)
	original=skimage.io.imread(picname, as_grey=True, plugin=None, flatten=True)
	image=img_as_float(original)
	image= 255*image
	
    
    #from skimage.filters import threshold_otsu, threshold_adaptive
	block_size = 90
	binary_adaptive = threshold_adaptive(image, block_size, offset=20)
	#convert binary picture to negative
	m= int(original.shape[0])
	n= int(original.shape[1])
	negative=np.zeros((m,n))

	for i in range(m):
		for j in range(n):
			if binary_adaptive[i][j]==0:
				negative[i][j]=1

	negative= negative>0
	
	seg2 = skimage.morphology.remove_small_objects(negative,min_size=150, connectivity=1, in_place=False)
	selem = diamond(20)
	closed = skimage.morphology.closing(seg2, selem)
	labeled=skimage.measure.label(closed, connectivity=1)
	
	#label image
	#from skimage.segmentation import find_boundaries
	#from skimage import measure

	labeled=skimage.measure.label(bin_closed, connectivity=1)
	props=skimage.measure.regionprops(labeled)

	def get_property_from_all_region(regions_list_obj, property_wanted):
		prop_list=[];
		#regions_property_list = []
		for current_region in regions_list_obj:
			current_prop=getattr(current_region, property_wanted)
			#if current_prop>50: #filter out small object noise
			prop_list.append(current_prop)
				#print prop_list[-1]
				#print getattr(current_region, property_wanted)
		return np.asarray(prop_list)

	perimeter_list= get_property_from_all_region(props, 'perimeter')
	area_list= get_property_from_all_region(props, 'area')
	#get perimenter/area ratio, 0.125 cutoff for outline/cell
	if(perimeter_list.size==area_list.size):
		arraylength=area_list.size
	else:
		arraylength=0

	ratiolist=np.empty(arraylength);
	for i in range(arraylength):
		ratiolist[i]= perimeter_list[i]/area_list[i]
		
	orien_list=get_property_from_all_region(props, 'orientation') #Angle between the X-axis and the major axis of the ellipse, in radius
    
	def data_filter(targetarray):
		temparray=[]
		for i in range(arraylength):
			if(ratiolist[i]<0.125 and perimeter_list[i]<1000. and area_list[i]<10000.):
				temparray.append(targetarray[i])
		return np.asarray(temparray)
		
	filtered_ratio= data_filter(ratiolist)
	filtered_perimeter= data_filter(perimeter_list)
	filtered_area=data_filter(area_list)
	filtered_orientation=data_filter(orien_list)
		

	os.chdir(savepath)
	resultfile= open(picname+'.txt',"w+")
	resultfile.write('\n ratio\n')
	resultfile.write(np.array_str(filtered_ratio))
	resultfile.write('\n perimeter\n')
	resultfile.write(np.array_str(filtered_perimeter))
	resultfile.write('\n area\n')
	resultfile.write(np.array_str(filtered_area))
	resultfile.write('\n orientation\n')
	resultfile.write(np.array_str(filtered_orientation))
	resultfile.close()
	import scipy.misc
	scipy.misc.imsave(picname+'_processed.png', bin_closed)
	
#only takes .png format file
for fichier in filelist[:]: # filelist[:] makes a copy of filelist.
    if not(fichier.endswith(".tif")): #modify for different format here
        filelist.remove(fichier)
    if (fichier.endswith(".tif")):
        image_processing(fichier,picpath, savepath)