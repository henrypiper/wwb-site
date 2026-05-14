const { app, BrowserWindow } = require("electron")

const path = require("path")

function createWindow() {

    const win = new BrowserWindow({

        width: 1400,
        height: 1000
    })

    win.loadFile(
        "index.html"
    )
}

app.whenReady().then(() => {

    createWindow()
})