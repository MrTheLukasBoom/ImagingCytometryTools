import pandas as pd
import os
import scandir as sd

import numpy as np
import shapely.geometry
import warnings
import re

warnings.simplefilter(action='ignore', category=FutureWarning)

#gets protein markers from a cellprofiler file
def get_markers_from_segmentation(Cells): # Helper funktion to get the markers from the segmentation dataset
    first_column = list(Cells.columns.values.tolist()) # gets you the keys from a pd df as list
    clean_markers = [] # empty list for markers
    for element in first_column: # gets you each element in the key list
        marker_cond = re.findall('MeanIntensity_', element) # Here only a condition to find the markers
        if bool(marker_cond) == True: # if there is an element that fits the description do the following
            marker = element[element.find('MeanIntensity_'):] # find all the symbols after mean intensity
            marker_str = str(marker) # turns marker into strings for the list
            clean_markers.append(marker_str) # append to marker list
    return(clean_markers) # returns marker list

# for mostly round cells
def cell_to_organell_basic(Cells, Cytoplasm, Nucleus, Nucleus_count):

    print('I am working :)')

    #create unique list of names of images
    UniqueNames_Full_cell = Cells.ImageNumber.unique() #creates a list of all unique images
    UniqueNames_Cytoplasm = Cytoplasm.ImageNumber.unique() #creates a list of all unique images
    UniqueNames_Nucleus = Nucleus.ImageNumber.unique() #creates a list of all unique images

    #create a data frame dictionary to store your data frames
    DataFrameDict_Full_cell = {elem: pd.DataFrame() for elem in UniqueNames_Full_cell} #creates a dictionary of all unique images
    DataFrameDict_Cytoplasm = {elem: pd.DataFrame() for elem in UniqueNames_Cytoplasm} #creates a dictionary of all unique images
    DataFrameDict_Nucleus = {elem: pd.DataFrame() for elem in UniqueNames_Nucleus} #creates a dictionary of all unique images

    #creates a data frame to store matched subcellular locations
    columns = ['ImageNumber','Location_Center_X','Location_Center_Y','AreaShape_MinFeretDiameter','AreaShape_MaxFeretDiameter',] #list for essential values and markers
    for markers in get_markers_from_segmentation(Cells): #get all markers
        columns.append(markers + '_Cell') #creates a column for the full cell
        columns.append(markers + '_Cytoplasm') #creates a column for the cytoplasm
        columns.append(markers + '_Nucleus') #creates a column for the nucleus

    single_nuclear_cells = pd.DataFrame(columns=columns) #empty dataframe for all markers and subcellular locations

    #Resets indexes for image blocks and they identefied objects
    for key in DataFrameDict_Full_cell.keys():
        DataFrameDict_Full_cell[key] = Cells[:][Cells.ImageNumber == key].reset_index()

    for key in DataFrameDict_Cytoplasm.keys():
        DataFrameDict_Cytoplasm[key] = Cytoplasm[:][Cytoplasm.ImageNumber == key].reset_index()

    for key in DataFrameDict_Nucleus.keys():
        DataFrameDict_Nucleus[key] = Nucleus[:][Nucleus.ImageNumber == key].reset_index()

    #Takes connectet images and they identefied objects form from the Dictionary
    for key, value in DataFrameDict_Full_cell.items():

        x_cell_t = DataFrameDict_Full_cell[key]['Location_Center_X'].to_list() #gets all x positions of cells on a image
        y_cell_t = DataFrameDict_Full_cell[key]['Location_Center_Y'].to_list() #gets all y positions of cells on a image
        position_cells = np.array(list(zip(x_cell_t, y_cell_t))) #creates an array of all the x and y positions of the cells

        x_cytoplasm_t = DataFrameDict_Cytoplasm[key]['Location_Center_X'].to_list() #gets all x positions of cytoplasms on a image
        y_cytoplasm_t = DataFrameDict_Cytoplasm[key]['Location_Center_Y'].to_list() #gets all y positions of cytoplasms on a image
        position_cytoplasm = np.array(list(zip(x_cytoplasm_t, y_cytoplasm_t))) #creates an array of all the x and y positions of the cytoplasms

        x_nucleus_t = DataFrameDict_Nucleus[key]['Location_Center_X'].to_list() #gets all x positions of nuclei on a image
        y_nucleus_t = DataFrameDict_Nucleus[key]['Location_Center_Y'].to_list() #gets all y positions of nuclei on a image
        position_nucleus = np.array(list(zip(x_nucleus_t, y_nucleus_t))) #creates an array of all the x and y positions of the nuclei
        
        count_cell = -1 #counter
        for cell in position_cells: #goes throw all cell positions
            cell_diameter = DataFrameDict_Full_cell[key]['AreaShape_MinFeretDiameter'].to_list()[count_cell] #creates the smallest possible cell diameter
            cell_shape = shapely.geometry.Point(cell).buffer(cell_diameter/2) #creates a circle representing the cell area
            count_cell = count_cell + 1 #adds a counter to the counter

            count_cytoplasm = -1 #counter
            for cytoplasm in position_cytoplasm: #goes throw all cytoplasm positions
                cytoplasm_position = shapely.geometry.Point(cytoplasm) #creates a point at the center of the cytoplasm object
                count_cytoplasm = count_cytoplasm + 1 #adds a counter to the counter

                if cytoplasm_position.within(cell_shape) == True: #checks if the center of the cytoplasm is within the cell

                    count_nucleus = -1 #counter
                    nucleus_list = [] #list of all found nuclei
                    for nucleus in position_nucleus: #goes throw all nuclei positions
                        nucleus_position = shapely.geometry.Point(nucleus)
                        count_nucleus = count_nucleus + 1 #adds a counter to the counter

                        if nucleus_position.within(cell_shape) == True: #checks if the center of the nucleus is within the cell
                            nucleus_list.append(count_nucleus)

                    if len(nucleus_list) == Nucleus_count: #checks the lenth of the nucleus list

                        new_row = {}  # Creates a new Row for all the localistions

                        ImageNumber = DataFrameDict_Full_cell[key]['ImageNumber'].to_list()[count_cell]
                        Location_Center_X = DataFrameDict_Full_cell[key]['Location_Center_X'].to_list()[count_cell]
                        Location_Center_Y = DataFrameDict_Full_cell[key]['Location_Center_Y'].to_list()[count_cell]
                        AreaShape_MinFeretDiameter = DataFrameDict_Full_cell[key]['AreaShape_MinFeretDiameter'].to_list()[count_cell]
                        AreaShape_MaxFeretDiameter = DataFrameDict_Full_cell[key]['AreaShape_MaxFeretDiameter'].to_list()[count_cell]

                        new_row.update({'ImageNumber': ImageNumber,
                                        'Location_Center_X': Location_Center_X,
                                        'Location_Center_Y': Location_Center_Y,
                                        'AreaShape_MinFeretDiameter': AreaShape_MinFeretDiameter,
                                        'AreaShape_MaxFeretDiameter': AreaShape_MaxFeretDiameter})
                        
                        # adds the mean intenitys to the new row
                        for marker in get_markers_from_segmentation(Cells):
                            MeanIntensity_Cell = DataFrameDict_Full_cell[key]['Intensity_' + marker].to_list()[count_cell]
                            MeanIntensity_Cytoplasm = DataFrameDict_Cytoplasm[key]['Intensity_' + marker].to_list()[count_cytoplasm]
                            MeanIntensity_Nucleus = DataFrameDict_Nucleus[key]['Intensity_' + marker].to_list()[nucleus_list[0]]

                            new_row.update({marker + '_Cell': MeanIntensity_Cell,
                                       marker + '_Cytoplasm': MeanIntensity_Cytoplasm,
                                       marker + '_Nucleus': MeanIntensity_Nucleus})
                    
                        single_nuclear_cells.loc[len(single_nuclear_cells)] = new_row #adds the new row to the dataframe
                    break
             
    return(single_nuclear_cells)

def neigboorhood(Cells):
    print('I am looking for my friends :)')

    # create unique list of names of images
    UniqueNames_Full_cell = Cells.ImageNumber.unique()  # creates a list of all unique images

    # create a data frame dictionary to store your data frames
    DataFrameDict_Full_cell = {elem: pd.DataFrame() for elem in UniqueNames_Full_cell}  # creates a dictionary of all unique images

    # Resets indexes for conected images and they identefied objects
    for key in DataFrameDict_Full_cell.keys():
        DataFrameDict_Full_cell[key] = Cells[:][Cells.ImageNumber == key].reset_index()

    Neigboorhood = []
    Cell_number = []

    # Takes connectet images and they identefied objects form from the Dictionary
    for key, value in DataFrameDict_Full_cell.items():

        x_cell_t = DataFrameDict_Full_cell[key]['Location_Center_X'].to_list()
        y_cell_t = DataFrameDict_Full_cell[key]['Location_Center_Y'].to_list()
        position_cells = np.array(list(zip(x_cell_t, y_cell_t)))

        count_cell = -1
        for cell in position_cells:
            cell_position = shapely.geometry.Point(cell)
            neighborhood_radius = DataFrameDict_Full_cell[key]['AreaShape_MaxFeretDiameter'].mean()
            cell_neighborhood = shapely.geometry.Point(cell).buffer(neighborhood_radius * 1.5)
            count_cell = count_cell + 1
            Cell_number.append(count_cell)

            Whats_in_the_hood = []
            count_other_cell = -1
            for other_cell in position_cells:
                other_cell_position = shapely.geometry.Point(other_cell)
                count_other_cell = count_other_cell + 1

                if other_cell_position == cell_position:
                    continue
                elif other_cell_position.within(cell_neighborhood) == True:
                    Whats_in_the_hood.append(count_other_cell)

            Neigboorhood.append(Whats_in_the_hood)

    Cells['Neigboorhood'] = Neigboorhood
    Cells['Cell_number'] = Cell_number

    return(Cells)


# gives you the neigbooring cell types
def neigboorhood_cell_type(Cell_type, Subtype,file):

    Neigboorhood_fin= []
    for index, cell in file.iterrows():

        if cell['Cell_types'] == Cell_type and cell['immune_type'] == Subtype:

            Neigboorhood = re.split(r',', cell['Neigboorhood'].replace('[', '').replace(']', ''))

            Neigboorhood_list = []
            for x in Neigboorhood:
                try:
                    Neigboorhood_list.append(int(float(x)))
                except ValueError:
                    pass


            Neigboorhood_cell = []
            for index, cell in file.iterrows():

                if cell['Cell_number'] in Neigboorhood_list:
                    Neigboorhood_cell.append(cell['Cell_types'])

            Neigboorhood_fin.append(Neigboorhood_cell)
            print(Neigboorhood_cell)

        else:
            Neigboorhood_fin.append('currently not of interest')

    return(Neigboorhood_fin)


folder_dir = r'D:\ATF6'# folder directory

#first neighborhood analysis
for paths, dirs, files in sd.walk(folder_dir): #goes throw all files and folders in given directory

    for file in os.listdir(paths): #goes throw all files in a folder
        filedir = os.path.join(paths, file) #returns fuull file directory

        if filedir.endswith(".csv"):# returns all files that end with txt

            filename = os.path.basename(file) # gives you the file name
            filename_string = str(filename)

            if 'RunCellpose_C' in filename_string: # checks for a condition in the string
                print(filedir)

                filedir_string = str(filedir)[:-len(filename)-5] # creates a file directory string

                filedir_images_string = filedir_string + r'\neigboorhood' # creates a new directory

                if os.path.isdir(filedir_images_string) == True: #checks if the new directory allready exists
                    pass
                else:
                    os.makedirs(filedir_images_string) # creates the new directory

                neigboorhood_all = neigboorhood(pd.read_csv(filedir)) # calculates the neighborhood
                neigboorhood_all.to_csv(filedir_images_string + '/' + filename_string[:-18] + '_neighborhood.csv') # exports the analysis

#Matching subcellular locations
for paths, dirs, files in sd.walk(folder_dir): #goes throw all files and folders in given directory

    for file in os.listdir(paths): #goes throw all files in a folder
        filedir = os.path.join(paths, file) #returns fuull file directory

        if filedir.endswith(".csv"): # returns all files that end with txt

            filename = os.path.basename(file) # gives you the file name
            filename_string = str(filename)

            if 'RunCellpose_C' in filename_string: # checks for a condition in the string
                dir_list = [] # creates a list to hold the other directories

                dir_list.append(filedir)
                filedir_string = str(filedir)[:-len(filename)-5] # creates a file directory string

                filedir_images_string = filedir_string + r'\subcellular localisation' # creates a new directory

                if os.path.isdir(filedir_images_string) == True: #checks if the new directory allready exists
                    pass
                else:
                    os.makedirs(filedir_images_string) # creates the new directory

                for paths, dirs, files in sd.walk(filedir_string + '/csv'):  # goes throw all files and folders in given directory

                    for file in os.listdir(paths):  # goes throw all files in a folder
                        filedir = os.path.join(paths, file)
                        filedir_string = str(filedir) # creates a file directory string

                        if 'RunCellpose_N' in filedir_string: # checks for a condition in the other files
                            dir_list.append(filedir)
                        if 'Cytoplasm' in filedir_string: # checks for a condition in the other files
                            dir_list.append(filedir)

                        if len(dir_list) == 3: # if three files are found the analisis is done

                            print(dir_list)

                            Full_cell = pd.read_csv(dir_list[0]) # reads the found files
                            Cytoplasm = pd.read_csv(dir_list[1])
                            Nucleus = pd.read_csv(dir_list[2])

                            single_cells_and_organells = cell_to_organell_basic(Full_cell, Cytoplasm, Nucleus,1) # matches subcellular locations
                            single_cells_and_organells.to_csv(filedir_images_string + '/' + filename_string[:-18] +'_single_cells_and_organells.csv') # exports the file

#second neighborhood analysis
for paths, dirs, files in sd.walk(folder_dir): #goes throw all files and folders in given directory

    for file in os.listdir(paths): #goes throw all files in a folder
        filedir = os.path.join(paths, file) #returns fuull file directory

        file_list = []
        if filedir.endswith("single_cells_and_organells.csv"): # returns all files that end with txt

            file_list.append(filedir)

            filename = os.path.basename(file)
            filename_string = str(filename)
            filedir_string = str(filedir)[:-len(filename)-1]

            filedir_images_string = filedir_string[:-len('subcellular localisation/')] + r'\subcellular localisation and neigboorhood'

            if os.path.isdir(filedir_images_string) == True:
                pass
            else:
                os.makedirs(filedir_images_string)

        for file in file_list:
            print(file)

            filename = os.path.basename(file)
            filename_string = str(filename)
            filedir_string = str(filedir)[:-len(filename) - 1]
            filedir_images_string = filedir_string[:-len('subcellular localisation/')] + r'\subcellular localisation and neigboorhood'

            df = pd.read_csv(filedir)
            df = df.drop('Unnamed: 0', axis=1)

            neigboorhood_sub = neigboorhood(df)
            neigboorhood_sub.to_csv(filedir_images_string + '/' + filename_string[:-len('single_cells_and_organells')-5] + '_subcell_neighborhood.csv')
