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

import numpy as np
import skimage
import skimage.io
import os, sys
from matplotlib.patches import Ellipse
from PIL import Image



def image_processing(filename):
	#adapted from Dianmu Zhang
	
	#image processing part
	#get threshold from cummulative historgram
    #filename='pic1.jpg'
	#os.chdir(picpath)
	original=skimage.io.imread(filename, as_grey=True, plugin=None, flatten=True)
	image=img_as_float(original)
	image= 255*image
	equalized= skimage.exposure.equalize_hist(image, nbins=256, mask=None)
	n, bins, patches= plt.hist(equalized.ravel(), bins=256, normed=1, histtype='step', cumulative=True) #step, normalized to 1

	nlist= n.tolist()
	binlist=bins.tolist()
	forecutoff,backcutoff=0,0
	for i in range(len(nlist)):
	    if(abs(nlist[i]-0.01)<0.005): #0.006 works for pic1
	        forecutoff=binlist[i]
	    if(abs(nlist[i]-0.80)<0.05):#0.80 works for pic1
	        backcutoff=binlist[i]
	        break
	
	#safty check, in case of extreme situations, assign value directly
	if(forecutoff==0):
		forecutoff=0.015
		
	if(backcutoff==0):
		backcutoff=0.75
		#if you'd like get a notification in extreme cases, uncomment below
		#raise Exception('low contrast image')
		
	# make segmentation using edge-detection and watershed
	edges = sobel(original)
	markers = np.zeros_like(original)
	foreground, background = 1, 2

	markers[equalized >backcutoff]= background
	markers[equalized <forecutoff]= foreground

	ws = watershed(edges, markers)
	seg1 = ndi.label(ws == foreground)[0]
	#clean out small objects
	seg2 = skimage.morphology.remove_small_objects(seg1,min_size=500, connectivity=1, in_place=False) #lower min_size=250
	#from skimage.morphology import disk,square,diamond
	selem = disk(10)
	closed = skimage.morphology.closing(seg2, selem)
	#covert closed to binary mask
	bin_closed= closed>1 
    
    
	#label image
	#from skimage.segmentation import find_boundaries
	#from skimage import measure

	labeled=skimage.measure.label(bin_closed, connectivity=1)
	props=skimage.measure.regionprops(labeled)
	

	list_cells=[]
	for region in props:
		current_perimeter=getattr(region, 'perimeter')
		current_area=getattr(region, 'area')
		current_orientation=getattr(region, 'orientation')
		center = getattr(region, 'centroid') #[y0, x0]
		long_axis= getattr(region, 'major_axis_length')
		short_axis=getattr(region, 'minor_axis_length')
		if current_perimeter/current_area<0.125:
			current_cell=cell(center=center, orientation=current_orientation, long_axis=long_axis, short_axis=short_axis)
			list_cells.append(current_cell)
	return list_cells

			


	


class microscope_experiment():
	"""
	Needs the nd2 file to be exported as pictures in 
	'directory'
	as tif, apply LUTs, and index order is T, XY, C
	"""
	def __init__(self, media, time_interval_min, directory):
		
		self.time_interval=time_interval_min
		self.media=media
		self.list_microcolonies=[]
		
		#Organize images
		#by frame
		list_frames=[]
		for file in os.listdir(directory):
			if file.endswith(".tif"):
				file1=file.split("XY") #[xxxxxxT##, ##C#xxx]
				file2=file1[1].split("C")
				frame=file2[0]
				list_frames.append(frame)		
		for frame in list(set(list_frames)):
			images=[]
			for file in os.listdir(directory):	
				if file.endswith(".tif") and frame in file:
					images.append(directory+"/"+file)
			self.list_microcolonies.append(microcolony(images, time_interval_min))			
	"""
	def save(self, format='txt'):
		 for pic in self.list_picture: 
			#write in txt file str(pic.to_save())
	"""
class microcolony():
	def __init__(self, list_image_files, time_interval_min):
		self.list_images=[]
		
		#compute list microscope_image objects from list files
		for file in list_image_files:
			name=file.split("/")
			file1=name[-1].split("T")
			file2=file1[1].split("XY")
			index=int(file2[0])
			time=index*time_interval_min
			
			self.list_images.append(microscope_image(file, time))	
			microscope_image(file, time).display_image_processing()
		
class microscope_image():
	def __init__(self, filename, time):
		self.time=time
		self.filename=filename
		
		
	def get_cells(self):
		list_cells=image_processing(self.filename)
		return list_cells
	
	def display_image_processing(self):
		print self.filename
		
		#convert to png for matplotlib
		im_tiff=skimage.io.imread(self.filename)#, as_grey=True)
		skimage.io.use_plugin('matplotlib')
		skimage.io.imsave(self.filename+".png", im_tiff)

		im = plt.imread(self.filename+".png")
		# Create a figure. Equal aspect so circles look circular
		fig,ax = plt.subplots(1)
		ax.set_aspect('equal')

		# Show the image
		ax.imshow(im)
		
		list_cells=self.get_cells()
		for cell in list_cells:
			print str(cell)
			ellipse = Ellipse(xy=(cell.center[1], cell.center[0]), width=cell.short_axis, height=cell.long_axis, 
                        edgecolor='r', angle=cell.orientation)
			ax.add_patch(ellipse)
		
		plt.show()
		os.remove(self.filename+".png")
		
	"""
	def to_save(self): 
		for cell in cell_obj_list: 
			res.append(cell.to_save()) 
		return res
	
	def plot_results():
		pass
	"""
	

class cell():
	def __init__(self, center, orientation, long_axis, short_axis):
		self.long_axis=long_axis
		self.short_axis=short_axis
		self.center=center
		self.orientation=orientation
	"""
	def to_save(self): 
		return {'perimeter': self.perimeter///}
	"""
	def __str__(self):
		return "Cell at (x="+str(self.center[1])+" ,y= "+str(self.center[0])+"), orientation= "+str(self.orientation)+",axis=("+str(self.short_axis)+","+str(self.long_axis)+")"


#Customerization field, change as needed
#file handling
#import os, sys
picpath="/Users/laura/Documents/Dropbox/Ladam@Klavins/microscopy/w303a/20160322"
savepath="/Users/laura/Documents/Dropbox/Ladam@Klavins/microscopy/w303a/20160322/Results"

microscope_experiment("SC", "3", picpath)


