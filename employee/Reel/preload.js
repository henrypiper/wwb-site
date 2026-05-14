const { contextBridge } = require("electron")
const { spawn } = require("child_process")
const fs = require("fs")
const path = require("path")

contextBridge.exposeInMainWorld(
    "electronAPI",
    {

        generateVideo: async (
            question,
            story,
            videoPath
        ) => {

            return new Promise((resolve, reject) => {

                const inputDir =
                    path.join(
                        __dirname,
                        "python",
                        "input"
                    )

                // SAVE TEXT FILES
                fs.writeFileSync(
                    path.join(inputDir, "question.txt"),
                    question
                )

                fs.writeFileSync(
                    path.join(inputDir, "story.txt"),
                    story
                )

                // COPY VIDEO
                fs.copyFileSync(
                    videoPath,
                    path.join(inputDir, "video.mp4")
                )

                // RUN PYTHON
                const py = spawn(
                    "python",
                    [
                        path.join(
                            __dirname,
                            "python",
                            "reel_generator.py"
                        )
                    ]
                )

                py.stdout.on("data", (data) => {

                    console.log(
                        data.toString()
                    )
                })

                py.stderr.on("data", (data) => {

                    console.error(
                        data.toString()
                    )
                })

                py.on("close", (code) => {

                    if (code === 0) {

                        resolve(
                            path.join(
                                __dirname,
                                "python",
                                "output",
                                "final_reel.mp4"
                            )
                        )

                    } else {

                        reject(
                            "Python failed"
                        )
                    }
                })
            })
        }
    }
)
