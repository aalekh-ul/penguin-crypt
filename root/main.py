from project import create_project

app = create_project()

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)