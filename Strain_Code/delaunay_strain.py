"""
May 2018
Take a set of velocities, establish delaunay triangles, 
solve a linear inversion problem for the components of the velocity gradient tensor
at the centroid of each triangle. 
The strain rate tensor and the rotation tensor can be readily computed 
from the symmetric and anti-symmetric parts of the velocity gradient tensor. 
Plot the outputs. 

Following a technique learned in Brad Hagar's geodynamics class, and 
modeled off of advice from 2007 Journal of Geodynamcis paper:
ftp://ftp.ingv.it/pub/salvatore.barba/RevEu/Cai_StrainBIFROST_2007.pdf
"""

import numpy as np
from scipy.spatial import Delaunay
from numpy.linalg import inv, det
import subprocess, sys
import strain_tensor_toolbox




# ----------------- COMPUTE -------------------------

def compute(myVelfield, MyParams):
	print("Computing strain via delaunay method.");
	z = np.array([myVelfield.elon,myVelfield.nlat]);
	z = z.T;
	tri=Delaunay(z);

	triangle_vertices = z[tri.simplices];
	trishape = np.shape(triangle_vertices);  # 516 x 3 x 2, for example

	# We are going to solve for the velocity gradient tensor at the centroid of each triangle. 
	centroids=[];
	for i in range(trishape[0]):
		xcor_mean = np.mean([triangle_vertices[i,0,0],triangle_vertices[i,1,0],triangle_vertices[i,2,0]]);
		ycor_mean = np.mean([triangle_vertices[i,0,1],triangle_vertices[i,1,1],triangle_vertices[i,2,1]]);
		centroids.append([xcor_mean,ycor_mean]);
	xcentroid=[x[0] for x in centroids];
	ycentroid=[x[1] for x in centroids];


	# Initialize arrays.
	I2nd=[];
	rot=[];
	max_shear=[];
	e1=[]; # eigenvalues
	e2=[];
	v00=[];  # eigenvectors
	v01=[];
	v10=[];
	v11=[];
	dilatation=[];


	# for each triangle:
	for i in range(trishape[0]):

		# Get the velocities of each vertex (VE1, VN1, VE2, VN2, VE3, VN3)
		# Get velocities for Vertex 1 (triangle_vertices[i,0,0] and triangle_vertices[i,0,1])
		xindex1 = np.where(myVelfield.elon==triangle_vertices[i,0,0])
		yindex1 = np.where(myVelfield.nlat==triangle_vertices[i,0,1])
		index1=np.intersect1d(xindex1,yindex1);
		xindex2 = np.where(myVelfield.elon==triangle_vertices[i,1,0])
		yindex2 = np.where(myVelfield.nlat==triangle_vertices[i,1,1])
		index2=np.intersect1d(xindex2,yindex2);
		xindex3 = np.where(myVelfield.elon==triangle_vertices[i,2,0])
		yindex3 = np.where(myVelfield.nlat==triangle_vertices[i,2,1])
		index3=np.intersect1d(xindex3,yindex3);

		VE1=myVelfield.e[index1[0]]; VN1=myVelfield.n[index1[0]];
		VE2=myVelfield.e[index2[0]]; VN2=myVelfield.n[index2[0]];
		VE3=myVelfield.e[index3[0]]; VN3=myVelfield.n[index3[0]];
		obs_vel = np.array([[VE1],[VN1],[VE2],[VN2],[VE3],[VN3]]);

		# Get the distance between centroid and vertex (in km)
		dE1 = (triangle_vertices[i,0,0]-xcentroid[i])*111.0*np.cos(np.deg2rad(ycentroid[i]));
		dE2 = (triangle_vertices[i,1,0]-xcentroid[i])*111.0*np.cos(np.deg2rad(ycentroid[i]));
		dE3 = (triangle_vertices[i,2,0]-xcentroid[i])*111.0*np.cos(np.deg2rad(ycentroid[i]));
		dN1 = (triangle_vertices[i,0,1]-ycentroid[i])*111.0;
		dN2 = (triangle_vertices[i,1,1]-ycentroid[i])*111.0;
		dN3 = (triangle_vertices[i,2,1]-ycentroid[i])*111.0;

		Design_Matrix = np.array([[1,0,dE1,dN1,0,0],[0,1,0,0,dE1,dN1],[1,0,dE2,dN2,0,0],[0,1,0,0,dE2,dN2],[1,0,dE3,dN3,0,0],[0,1,0,0,dE3,dN3]]);

		# Invert to get the components of the velocity gradient tensor. 
		DMinv = inv(Design_Matrix);
		vel_grad = np.dot(DMinv, obs_vel);  # this is the money step. 
		VE_centroid=vel_grad[0][0];
		VN_centroid=vel_grad[1][0];
		dVEdE=vel_grad[2][0];
		dVEdN=vel_grad[3][0];
		dVNdE=vel_grad[4][0];
		dVNdN=vel_grad[5][0];


		# The components that are easily computed
		[exx, exy, eyy, rotation] = strain_tensor_toolbox.compute_strain_components_from_dx(dVEdE, dVNdE, dVEdN, dVNdN);

		# # Compute a number of values based on tensor properties. 
		I2nd_tri = np.log10(np.abs(strain_tensor_toolbox.second_invariant(exx, exy, eyy)));
		I2nd.append(I2nd_tri);
		[e11, e22, v] = strain_tensor_toolbox.eigenvector_eigenvalue(exx, exy, eyy);

		e1.append(e11);
		e2.append(e22);
		rot.append(abs(rotation));
		max_shear.append((e11 - e22)/2);
		v00.append(v[0][0]);
		v10.append(v[1][0]);
		v01.append(v[0][1]);
		v11.append(v[1][1]);
		dilatation.append(e11+e22);

	print("Success computing strain via delaunay method.\n");


	return [xcentroid, ycentroid, triangle_vertices, I2nd, max_shear, rot, e1, e2, v00, v01, v10, v11, dilatation];




