from app import create_app


# ACA SE INICIA LA APP 
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
