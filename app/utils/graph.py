import numpy as np
import streamlit as st
import plotly.graph_objs as go
import calendar

from sklearn.preprocessing import StandardScaler


def get_b1(b0, b2):
    # b0, b1 list of x, y coordinates
    if len(b0) != len(b2) != 2:
        raise ValueError('b0, b1 must be lists of two elements')
    b1 = 0.5 * (np.asarray(b0)+np.asarray(b2))+\
         0.5 * np.array([0,1.0]) * np.sqrt(3) * np.linalg.norm(np.array(b2)-np.array(b0))
    return b1.tolist()


def dim_plus_1(b, w):#lift the points b0, b1, b2 to 3D points a0, a1, a2 (see Gallier book)
    #b is a list of 3 lists of 2D points, i.e. a list of three 2-lists 
    #w is a list of numbers (weights) of len equal to the len of b
    if not isinstance(b, list) or  not isinstance(b[0], list):
        raise ValueError('b must be a list of three 2-lists')
    if len(b) != len(w)   != 3:
        raise ValueError('the number of weights must be  equal to the nr of points')
    else:
        a = np.array([point + [w[i]] for (i, point) in enumerate(b)])
        a[1, :2] *= w[1]
        return a


def Bezier_curve(bz, nr): #the control point coordinates are passed in a list bz=[bz0, bz1, bz2] 
    # bz is a list of three 2-lists 
    # nr is the number of points to be computed on each arc
    t = np.linspace(0, 1, nr)
    #for each parameter t[i] evaluate a point on the Bezier curve with the de Casteljau algorithm
    N = len(bz) 
    points = [] # the list of points to be computed on the Bezier curve
    for i in range(nr):
        aa = np.copy(bz) 
        for r in range(1, N):
            aa[:N-r,:] = (1-t[i]) * aa[:N-r,:] + t[i] * aa[1:N-r+1,:]  # convex combination of points
        points.append(aa[0,:])                                  
    return np.array(points)


def Rational_Bezier_curve(a, nr):
    discrete_curve = Bezier_curve(a, nr ) 
    return [p[:2]/p[2] for p in discrete_curve]


@st.experimental_memo
def get_graph_data(query_results):
    # Sort papers by date
    nodes = sorted(query_results, key=lambda d: d['year'] + '-' + d['month'])
    nodes = [
        {
            'title': paper['title'],
            'nb_citations': len(paper['citations'].split(',')),
            'year': paper['year'],
            'month': paper['month'],
            'similarity_score': paper['similarity_score'],
            'sch_id': paper['sch_id'],
            'citations': paper['citations'],
            'index': i
        }
        for i, paper in enumerate(nodes)
    ]

    links = []
    sch_ids = [paper['sch_id'] for paper in nodes]

    for paper in nodes:
        links += [
            {
                'source': sch_ids.index(sch_id),
                'target': sch_ids.index(paper['sch_id']),
                'value': 10
            }
            for sch_id in list(set(sch_ids).intersection(set(paper['citations'].split(','))))
            if sch_id != "None"
        ]

    return (
        {
            'nodes': nodes,
            'links': links
        }
    )


@st.experimental_memo
def get_arc_graph(data):
    papers = data['nodes']
    L = len(data['nodes'])  # number of nodes (papers)
    labels = [item['title'] for item in data['nodes']]
    values = [item['nb_citations'] for item in data['nodes']]
    values_2d = [[val] for val in values]
    values_scaled = list(
        StandardScaler()
        .fit(values_2d)
        .transform(values_2d)
        .reshape(-1) * 6 + 10
    )
    values_scaled = list(np.clip(values_scaled, 1, 50))
    hover_text = [
        (
            f"<b>{paper['title']}</b><br>"
            f"<b>Citations:</b> {paper['nb_citations']}<br>"
            f"<b>Date:</b> {calendar.month_name[int(paper['month'])]} {paper['year']}<br>"
            f"<b>Similarity score:</b> {round(paper['similarity_score'], 2)}/1 "
        )
        for paper in data['nodes']

    ]
    year_max = max([int(paper['year']) for paper in data['nodes']])
    year_min = min([int(paper['year']) for paper in data['nodes']])

    edges = [(item['source'], item['target']) for item in data['links']]
    interact_strength = [item['value'] for item in data['links']]
    keys = sorted(set(interact_strength))
    widths = [0.5+k*0.25 for k in range(5)] + [2+k*0.25 for k in range(4)]+[3, 3.25, 3.75, 4.25, 5, 5.25, 7]
    d = dict(zip(keys, widths))  
    nwidths = [d[val] for val in interact_strength]

    color_scale = ['rgb(101,204,204)', 'rgb(255,0,102)']

    node_trace = dict(
        type='scatter',
        x=list(range(L)),
        y=[0]*L,
        mode='markers',
        marker=dict(size=values_scaled, 
                    color=[int(paper['year']) for paper in data['nodes']], 
                    colorscale=color_scale,
                    showscale=False,
                    line=dict(color='rgb(50,50,50)', width=0.75)),
        text=hover_text,
        hoverinfo='text'
    )
    colorbar_trace = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            colorscale=color_scale,
            showscale=True,
            cmin=-5,
            cmax=5,
            colorbar=dict(thickness=5, tickvals=[-5, 5], ticktext=[str(year_min), str(year_max)], outlinewidth=0)
        ),
        hoverinfo='none'
    )

    data = []
    tooltips = [] #list of strings to be displayed when hovering the mouse over the middle of the circle arcs
    xx = []
    yy = []

    X = list(range(L)) # node x-coordinates
    nr = 75 
    for i, (j, k) in enumerate(edges):
        if j < k:
            tooltips.append(f'interactions({labels[j]}, {labels[k]})={interact_strength[i]}')
        else:
            tooltips.append(f'interactions({labels[k]}, {labels[j]})={interact_strength[i]}')
        b0 = [X[j], 0.0]
        b2 = [X[k], 0.0]
        b1 = get_b1(b0, b2)
        a = dim_plus_1([b0, b1, b2], [1, 0.5, 1])
        pts = Rational_Bezier_curve(a, nr)
        xx.append(pts[nr//2][0]) #abscissa of the middle point on the computed arc
        yy.append(pts[nr//2][1]) #ordinate of the same point
        x,y = zip(*pts)
        
        data.append(dict(type='scatter',
                        x=x, 
                        y=y, 
                        name='',
                        mode='lines', 
                        line=dict(width=nwidths[i], color='#6b8aca', shape='spline'),
                        hoverinfo='none'
                        )
                    )
    data.append(dict(type='scatter',
                    x=xx,
                    y=yy,
                    name='',
                    mode='markers',
                    marker=dict(size=0.5, color='#6b8aca'),
                    text=tooltips,
                    hoverinfo='text'))
    data.append(node_trace)
    data.append(colorbar_trace)

    layout = dict(
        font=dict(size=10), 
        #width=2000,
        height=600,
        showlegend=False,
        xaxis=dict(anchor='y',
                showline=False,  
                zeroline=False,
                showgrid=False,
                tickvals=list(range(L)),
                ticktext=[
                    f'''<a target="_self" href="#section-{max(0, paper['index'])}">{paper['title'] if len(paper['title']) < 70 else paper['title'][:70]+"..."}</a>'''
                    for paper in papers
                ],
                tickangle=80,
                ),
        yaxis=dict(visible=False), 
        hovermode='closest',
        margin=dict(t=30, b=110, l=1, r=1),
        annotations=[dict(showarrow=False, 
                        text="",
                        xref='paper',     
                        yref='paper',     
                        x=0.05,  
                        y=-0.3,  
                        xanchor='left',   
                        yanchor='bottom',  
                        font=dict(size=10))
                                ]  
        )
    return go.FigureWidget(data=data, layout=layout)
