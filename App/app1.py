"""Script to generate a classification of multiple images and show the images and
their classification as a gallery. The current method uses Dash with python
 (and flask).
 To put in production do:
 gunicorn app1:server -b :7070 -t 1000
"""

import base64
import os
# import sh
from flask import Flask
#from flask_sslify import SSLify # redirects http to https

import dash
import dash_auth # Use only as a secure option
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import time
from production import predictor
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans


import plotly.graph_objs as go

import numpy as np
from collections import Counter

## IMPORT THE info prediccion HERE========================

infop = predictor()

## =============================================
USERNAME_PASSWORD = [['team14', 't34m14']] # Use only as a secure option

# Detecting and/or making the current image path
CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_DIRECTORY = os.path.join(CURRENT_FOLDER, 'app_uploaded_files')
# PREDICTIONS_DICT = dict()

SEED = 123

# Defining the styles of the boxes and their labels
SPAN_STYLE = {
        'background': 'none repeat scroll 0 0 #4D57DB',
            'border': '2px solid #ffffff',
            'border-radius': '25px',
            'color': 'White',
            'font-size': '20px',
            'font-weight': 'bold',
            'padding': '5px 15px',
            'position': 'absolute',
            'left': '-5px',
            'top': '-25px'
        }

BOX_STYLE = {
        'color':'green', 'border':'2px #4D57DB solid',
        'margin':'3%', 'padding':'3%',
        'position': 'relative',
        'display': 'inline-block', 
        'margin-top': 30, 
        'margin-bottom': 20,
        'margin-right':'2%',
        'margin-left':'2%',
        'width': '90%'
        }

INITIAL_MESSAGE = '''
                        
                            ### Welcome

                            Blood cell classification is one of the most challenging tasks in blood diagnosis. 
                            Performing the classification of the cells through the manual procedure is difficult, prone to errors, and time-consuming due to the involvement of human labor. 
                            Also, for the manual segmentation, the experts make use of the advanced equipment, which cannot be adopted in rural areas.

                            The application allows loading the images to be classified. Once the images are loaded, the user will have three (3) tabs available to interact with the loaded images 
                            
                            1. Classification-allows the user to view how the images were classified according to the types of cells available 
                            2. Chart-allows the user to quickly identify the amounts of images classified in each cell type with a bar chart and a pie chart.
                            3. Visual Analysis-the most interactive tab since it shows the user through a scatter diagram the type of cells images loaded divided by zones. When clicking at each point, which represents a peripheral blood cell, shows the loaded image file already classified.

                            Use this examples images to classification. [Blood Cells Images](https://github.com/Fag42/MinTIC-DS4A-Project---Team-14/blob/master/Examples/Examples.zip)

                           
                            '''

VISUAL_DESCRIPTION = """This is the most interactive tab, since it shows a scatter plot generated through the dimensionality reduction of
the deep features of the last layer of the CNN model using [t-SNE](https://lvdmaaten.github.io/tsne/). The background of the plot, which
is similar to a boundary decision graph, is made by implementing the k-means clustering technique to the (t-SNE components of the) uploaded cell
images along with 1000 training cells. Thus, every type of the loaded cell images is shown in a corresponding region. Clicking on 
each point, which represents a peripheral blood cell, displays the loaded image file already classified."""


#Creating image folders
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = [
    # Normalize the CSS
    "https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
    # Fonts
    "https://fonts.googleapis.com/css?family=Open+Sans|Roboto"
    "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
    # For production
    "https://cdn.rawgit.com/xhlulu/0acba79000a3fd1e6f552ed82edb8a64/raw/dash_template.css",
    # Custom CSS
    "https://cdn.rawgit.com/xhlulu/dash-image-processing/1d2ec55e/custom_styles.css",
]

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
#sslify = SSLify(server)  # redirects http to https
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)
# app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Use only as a secure option
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD)

# If you are assigning callbacks to components that are generated by other
# Callbacks (and therefore not in the initial layout), then you can suppress
# this exception by setting
app.config['suppress_callback_exceptions']=True

#_______________________________LAYOUT__________________________________________

# MAIN LAYOUT
app.layout = html.Div([

    # Banner
    html.Div([
        html.H2(
            'Blood Cell Classification',
            id='title',style={'color':'White'}
        ),
        html.Img( 
            src=app.get_asset_url("logods4all.svg"),
           # style={'backgroundColor':'Purple'}
        )
    ],
        className="banner",
        style={'color':'Black'}
    ),

    #  Image Uploader
    html.Div(className="container",
        children=[

            #Upload Images
            dcc.Upload(
            id='upload-image',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files'),
            ]),
            style={
                'width': '90%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '25px',
                'textAlign': 'center',
                'marginBottom':'10px',
                'marginLeft':'50px',
                #'margin' : 'auto',
            },
            # Allow multiple files to be uploaded
            multiple=True,
            accept='image/*'
        ),        
        dcc.Loading( id="loading-1",
            children=[
        html.Div(id='output_mrkdwn',          
                    children=dcc.Markdown(INITIAL_MESSAGE)),
        html.Div(id='output-image-upload'),
        html.Div(id='tabs-content', style = {'margin':'auto'}) ] ),

        ],
            style={#'float':'right',
                   'float':'middle',
                   'width':'70%',
                   },
        ),


])
# _________________________End of Layout__________________________________
# ________________________________________________________________________


'''_________________________Image layout___________________________________'''

## -------------------Build the gallery----------------------
def parse_contents(contents, filename, prediction):
    layout = html.Div([
        html.Div(className='gallery',
                 children=[
                     html.A(
                         target='_blank',
                         href=contents,
                         # HTML images accept base64 encoded strings in the same format
                         # that is supplied by the upload
                         children=html.Img(src=contents, width=360, height=363,
                                           style={'width': '100%',
                                                  'height': 'auto'})
                     ),
                    #  html.Div(filename,
                    #           style={'padding': 5,
                    #                  'textAlign': 'center',
                    #                  'font-size': '0.8em'}
                    #           ),
                 ],
                 style={
                     'margin': 5,
                     'border': '1px solid #ccc',
                     'float': 'left',
                     'width': 150,
                     'height': 150 # 190 if include filename
                     }
                 )
    ])

    return layout


'''______________________Image Uploader______________________'''

@app.callback([Output('output-image-upload', 'children'), Output('output_mrkdwn', 'children')],
              [Input('upload-image', 'contents')],
              [State('upload-image', 'filename')])

def update_output(list_of_contents, list_of_names):

    # Delete the previous files
    if os.listdir(UPLOAD_DIRECTORY):
        removefiles()

    # Save all the images
    if list_of_contents is not None:
        for c, n in zip(list_of_contents, list_of_names):
            save_file(n, c)

        # ==============Classification process ====================
        
        infop.prediction(UPLOAD_DIRECTORY)
        # print(infop.features.shape)

        infop.figure = make_plotClass()        

        # ========================================================

        # Automatic Tabs infered from the LABELS
        children = html.Div([
                    dcc.Tabs( id="tabs", value='tab-1', 
                    children=[
                        dcc.Tab(label='Help', value='tab-0'),                        
                        dcc.Tab(label='Classification', value='tab-1'),
                        dcc.Tab(label='Chart', value='tab-2'),
                        dcc.Tab(label='Visual analysis', value='tab-3'),
                        
                        ]
                        )
                    ])

        return children, True
    else:
        return None, dcc.Markdown(INITIAL_MESSAGE)


'''______________________Tabs______________________'''

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])

def render_content(tab):

    
    if tab == 'tab-2':
        
        # Count the frecuencies of each predicted label
        labels, values = count_images(infop.predictions_dict)           


        colors = ['red', 'orange', 'darkgreen', 'blue', 'purple', 
                    'orange', 'lightgreen', 'lightblue']


        out = html.Div([
            html.Div([
            html.Div([
                dcc.Graph(
                    figure={
                        'data':[
                            go.Bar(x=labels, y=values,
                                   textfont=dict(size=20),
                                   marker_color = colors)                                                           
                                                                                                                                             
                                            
                    ],
                'layout':go.Layout(
                   title="Bar Plot of Predictions"
                    )
                }          
            )],
                className="six columns",
                 ),
           html.Div([
                dcc.Graph(
                    figure={
                        'data':[
                            go.Pie(labels=labels, values=values,
                                   textfont=dict(size=20),
                                   marker = dict(colors = colors))
                    ],
                'layout':go.Layout(
                   title="Pie Chart of Predictions"
                    )
                }          
            )],
                className="six columns"
            ),
        ], className="row")
        ])
        
        return out

    elif tab == 'tab-1':
        child = list()
        for l in infop.labels:            
            child.append( html.Div( children = show_test(l) +
            [html.Span(l, className = 'index', style = SPAN_STYLE)],
             className = 'box', style = BOX_STYLE
             )
            )            

        return child

    elif tab == 'tab-3':
        child = html.Div([                   
                                                        
            html.H4("TSNE of the Deep Features",
                    style={'textAlign': 'center'}),
                    
                      
            html.Div([                
            html.Div([        
            dcc.Graph(id='names_images',
            figure = infop.figure),
            ],
                className="six columns",
                 ),          
         

            html.Div([
                    html.Img(id='click-image', src='children', height=300, 
                    width=300, hidden=True)
                ], 
                    style={'height': '450px', 'paddingtop':20, 'padding-left': '200px', 'display':'flex',
                    'justify-content': 'center', 'align-items': 'center' }, 
                    className="six columns",
                ),
            
            
            ], className="row"       
            
            ),                

            dcc.Markdown(VISUAL_DESCRIPTION,
                    style={'textAlign':'bottom'}),  
        ])

        return child       

    elif tab == 'tab-0':
        child = html.Div([                                                         
                    
            
            html.Div([
                    dcc.Markdown(INITIAL_MESSAGE)          
                
            ])

        ])            
        return child


'''______________________XXX______________________'''

#Count amount of Images
def count_images(PD):
    d = Counter(PD.values())
    labels = list(d.keys())
    values = list(d.values())
    return labels, values


def save_file(name, content):
    #Decode and store a file uploaded with Plotly Dash.
    data = content.encode('utf8').split(b';base64,')[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), 'wb') as fp:
        fp.write(base64.decodebytes(data))

#remove function
def removefiles():
    """Remove all files inside the UPLOAD_DIRECTORY"""
    for the_file in os.listdir(UPLOAD_DIRECTORY):
        file_path = os.path.join(UPLOAD_DIRECTORY, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def encode_image(image_file):
    encoded = base64.b64encode(open(image_file, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded.decode())

def show_test(clase):
    children = []
    for name,label in infop.predictions_dict.items():
        if label == clase:
            # out.append(html.H4(name))
            contents = encode_image(os.path.join(UPLOAD_DIRECTORY, name))
            children.append(parse_contents(contents, name, label))
    return children

# Data Loading and prediction
# @app.server.before_first_request
# def load_model():
#     global prediction
#     print("\nLoading before first request\n")
#     from production import prediction

def make_plotClass():

    # To avoid problem with 1D array
    if infop.features.ndim == 1:
        infop.features = infop.features.reshape(1,-1)

    features = np.concatenate( (infop.features_train, infop.features))

    im_embedded = TSNE(n_components=2, init='pca', random_state=SEED).fit_transform(features)



    # scale and move the coordinates so they fit [0; 1] range
    def scale_to_01_range(x):
        # compute the distribution range
        value_range = (np.max(x) - np.min(x))
        # move the distribution so that it starts from zero
        # by extracting the minimal value from all its values
        starts_from_zero = x - np.min(x)
        # make the distribution fit [0; 1] by dividing by its range
        return starts_from_zero / value_range

    # extract x and y coordinates representing the positions of the images on T-SNE plot
    tx = im_embedded[:, 0]
    ty = im_embedded[:, 1]

    tx = scale_to_01_range(tx)
    ty = scale_to_01_range(ty)
    
    infop.tx = tx[1000:]
    infop.ty = ty[1000:]
    

    # Clustering of the two tsne components
    kmeans = KMeans(init='k-means++', n_clusters=8, n_init=10,random_state=SEED)
    im_normalized = np.c_[tx,ty]
    kmeans.fit(im_normalized.astype('float64'))

    # Find the corresponding labels of the clusters
    tipos_train = np.array(infop.tipos_train)
    kmeans_labels=[None for x in range(8)]
    for tipo in set(tipos_train):
        idx = tipos_train==tipo
        tt = np.c_[tx[:1000][idx], ty[:1000][idx]]
        clu = kmeans.predict(np.mean(tt,axis=0).reshape(1,-1).astype('float64'))
        kmeans_labels[clu[0]]=tipo

    # Step size of the mesh. Decrease to increase the quality of the VQ.
    h = .002     # point in the mesh [x_min, x_max]x[y_min, y_max].

    # Plot the decision boundary. For that, we will assign a color to each
    x_min, x_max = im_normalized[:, 0].min(), im_normalized[:, 0].max()
    y_min, y_max = im_normalized[:, 1].min(), im_normalized[:, 1].max()
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    
    # Obtain labels for each point in mesh. Use last trained model.
    Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    # Color map from seaborn
    paleta = sns.color_palette("Set1", n_colors=8) # paleta para la dispersion

    # MAKE THE FIGURE USING PLOT.LY
    fig = go.Figure(data=go.Heatmap(
        z=Z,
        x = xx[0],
        y = xx[0],
        colorscale=paleta.as_hex(), opacity = 0.3,
        showscale=False,
        hoverinfo='none',
    ))
    for color,label in zip(paleta.as_hex(),kmeans_labels):
        ind = tipos_train == label
        fig.add_trace(go.Scatter(
            x = tx[:1000][ind],
            y = ty[:1000][ind],
            mode = 'markers',
            marker=dict(
                size = 15,
                symbol = 'circle',
                color = color,
                opacity = 1,
            ),
            name = label,
            opacity = 1,
            hoverinfo = 'none',
            visible = 'legendonly',
        ))

    print(infop.predictions_dict)    
    print(list(infop.predictions_dict.values()))
    for color,label in zip(paleta.as_hex(),kmeans_labels):
        ind = np.array(list(infop.predictions_dict.values())) == label

        a = -0.04
        b = -a
        smallx = (b-a)*np.random.random_sample(tx[1000:][ind].shape) + a
        smally = (b-a)*np.random.random_sample(tx[1000:][ind].shape) + a
        TX = tx[1000:][ind]+smallx
        TY = ty[1000:][ind]+smally
        tx[1000:][ind] = TX
        ty[1000:][ind] = TY

        # TX = tx[1000:][ind]
        # TY = ty[1000:][ind]

        fig.add_trace(go.Scatter(
            x = TX,
            y = TY,
            mode = 'markers',
            marker=dict(
                size = 10,
                symbol = 'circle',
                color = color,
                line=dict(color='black',width=1),
                opacity=0.5
            ),
            name = label,
            opacity = 1,
            hoverinfo = 'name',
            visible = True,
            showlegend=False,           
        ))
        
        
        
        


    fig.update_layout(autosize=True,
                    # width=600, height=600,
                    xaxis=dict(constrain='domain', range=[0,1], showticklabels=False),
                    yaxis=dict(scaleanchor="x", scaleratio=1, constrain='domain', range=[0,1], showticklabels=False),
                    margin=go.layout.Margin(l=3, r=3,b=3, t=3 ),
                    hovermode='closest',
                    # title="TSNE of the deep features",
                    # title_x=0.5,
                    )

    return fig





@app.callback([Output('click-image', 'src'),Output('click-image', 'hidden')],
             [Input('names_images', 'clickData')])
def callback_image(clickData):     
    
    if clickData is not None:
        files = np.array(list(infop.predictions_dict.keys()))
        y=clickData['points'][0]['y']
        x=clickData['points'][0]['x']
        idx = (infop.tx == x) & (infop.ty == y)
        archivo = files[idx]

        if archivo.size > 0:
            # print(archivo)
            # print(UPLOAD_DIRECTORY)
            return encode_image(os.path.join(UPLOAD_DIRECTORY,archivo[0])), False
        else:
            return None, True  
    else:
        return None, True 
    


    


if __name__ == '__main__':
    app.run_server(debug=True)
