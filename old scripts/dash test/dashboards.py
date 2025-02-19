def init_callbacks(dash_app):
    @dash_app.callback(
        Output('main-graph', 'figure'),
        Input('main-graph', 'id')  # Cambiato da 'none' a un input valido
    )
    def update_graph(_):
        df = pd.DataFrame({
            'Mese': ['Gen', 'Feb', 'Mar', 'Apr'],
            'Valore': [100, 120, 90, 150]
        })
        
        fig = px.line(df, x='Mese', y='Valore', title='Trend Mensile')
        return fig