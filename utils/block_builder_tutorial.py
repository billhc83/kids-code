import base64
from pathlib import Path
from utils.step_builder import build_step, intro_step, rect, circle
from utils.image_utils import img_to_b64

META = {
    'title': 'How to use the block builder',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = None

phantom = img_to_b64("static/graphics/phantom.png")
selected_phantom = img_to_b64("static/graphics/selected_phantom.png")
block_pallete = img_to_b64("static/graphics/block_pallete.png")
block = img_to_b64("static/graphics/block.png")
expression_selected = img_to_b64("static/graphics/expression_selected.png")
expression_pallete = img_to_b64("static/graphics/expression_pallete.png")
expression_blank = img_to_b64("static/graphics/expression_blank.png")
expression_filled = img_to_b64("static/graphics/expression_filled.png")
output = img_to_b64("static/graphics/output.png")
switch_to_editor = img_to_b64("static/graphics/switch_to_editor.png")


DRAWER_CONTENT = {
   
      "block_builder_tutorial": [
               {
                  "title": "🧱 Your Workspace",
                  "tip":" ",
                  "tabs": {
                    "mission": {
                      "label": "🧠 Mission",
                      "content": """
                          <h3>Let’s look around!</h3>
                          <p>This step is just about learning <b>where things are</b>.</p>
                          <p>No building yet 👍</p>
                                  """
                                },
                    "build": {
                      "label": "🔧 Build",
                      "content": """
                          <ul>
                          <li>Click the headers to open <b>Global</b>, <b>Setup</b>, and <b>Loop</b></li>
                          <li>Look for empty spots (these are called <b>phantoms 👻</b>)</li>
                          </ul>
                          """
                              },

                    "code": {
                      "label": "💻 Blocks",
                      "content": """
                          <p>Your workspace has 3 parts:</p>
                          <ul>
                          <li><b>Global</b> → where variables live 📦</li>
                          <li><b>Setup</b> → runs one time ▶️</li>
                          <li><b>Loop</b> → runs over and over 🔁</li>
                          </ul>
                          """
                            },
                    "test": {
                      "label": "🧪 Check",
                      "content": """
                          <p>Can you open and close all 3 sections?</p>
                          """
                            },
                    "tip": {
                      "label": "💡 Tip",
                      "content": """
                          <p>Click inside a section if you don’t see any 👻 phantoms.</p>
                          """
                          }
                    }
                  },

                  {
                    "title": "👻 Click a Phantom",
                    "tip":"",
                    "tabs": {
                      "mission": {
                        "label": "🧠 Mission",
                        "content": """
                            <h3>Place your first block!</h3>
                            <p>You will use a phantom 👻 to add something new.</p>
                            """
                                },
                      "build": {
                        "label": "🔧 Build",
                        "content": f"""
                            <ol>
                            <li>Click a 👻 phantom in <b>Global</b>
                              <br><img src="{phantom}" style="max-width:100%;height:auto;" />
                              <br><img src="{selected_phantom}" style="max-width:100%;height:auto;" />
                            </li>
                            <li>Look at the blocks that appear
                              <br><img src="{block_pallete}" style="height:auto;width:auto;max-width:100px;" />
                            </li>
                            <li>Click one to place it
                              <br><img src="{block}" style="max-width:100%;height:auto;" />
                            </li>
                            <li>Inside some blocks you can add expressions, click the expression slot
                              <br><img src="{expression_selected}" style="max-width:100%;height:auto;" />
                            </li>
                            <li>Look at the palette — it will show the expressions available
                              <br><img src="{expression_pallete}" style="height:auto;width:auto;max-width:100px;" />
                            </li>
                            <li>Click the value expression, it will now be inside your block</li>
                            <li>From here we can enter the value of myNumber — for this example we will use 5
                              <br><img src="{expression_blank}" style="max-width:100%;height:auto;" />
                              <br><img src="{expression_filled}" style="max-width:100%;height:auto;" />
                            </li>
                            <li>Now our line of code is finished, we can see it in the output section
                              <br><img src="{output}" style="height:auto;width:auto;max-width:150px;" />
                            </li>
                            <li>Go ahead and click <img src="{switch_to_editor}" style="height:1.2em;width:auto;vertical-align:middle;" /> to switch to the editor</li>
                            <li>You can see our code looks just like our output code</li>
                            <li>Instead of writing all this code we just used blocks</li>
                            </ol>
                            """
                                },
                      "code": {
                        "label": "💻 Blocks",
                        "content": """
                            <p>Phantoms 👻 are empty spots waiting for code.</p>
                            <p>Click one to tell the program <b>where</b> to add something.</p>
                            """
                                },
                      "test": {
                        "label": "🧪 Check",
                        "content": """
                            <p>Did a block appear where the phantom was? 🎉</p>
                            """
                                },
                      "tip": {
                        "label": "💡 Tip",
                        "content": """
                            <p>No blocks showing? Try clicking the phantom again.</p>
                            """
                                }
                    }
                  },

                  {
                  "title": "🎯 Pick from the Palette",
                  "tip":" ",
                  "tabs": {
                    "mission": {
                      "label": "🧠 Mission",
                      "content": """
                          <h3>Choose the right block.</h3>
                          <p>You will use the palette to pick blocks.</p>
                          """
                              },
                    "build": {
                      "label": "🔧 Build",
                      "content": """
                          <ol>
                          <li>Click a 👻 phantom in <b>Setup</b></li>
                          <li>Look at the palette</li>
                          <li>Click the correct block</li>
                          <li>Lets click the top phantom block. Lets make it say Serial.begin(9600)</li>
                          <li>Next click the bottom phantom block. Lets make it say Serial.println("Hello!")</li>
                          </ol>
                          """
                              },
                    "code": {
                      "label": "💻 Blocks",
                      "content": """
                          <p>The palette shows what you can use 🎨</p>
                          <p>It changes depending on what you click.</p>
                          """
                              },
                    "test": {
                      "label": "🧪 Check",
                      "content": """
                          <p>Each phantom should now have a block inside it 👍</p>
                          """
                              },
                    "tip": {
                      "label": "💡 Tip",
                      "content": """
                          <p>Picked the wrong one? Just remove it and try again 🔁</p>
                          """
                              }
                  }
                },

                {
                  "title": "🔢 Fill the Slots",
                  "tip":" ",
                  "tabs": {
                    "mission": {
                      "label": "🧠 Mission",
                      "content": """
                          <h3>Complete your block.</h3>
                          <p>You will fill in the missing pieces.</p>
                          """
                              },
                    "build": {
                      "label": "🔧 Build",
                      "content": """
                          <ol>
                          <li>Click the empty space inside a block</li>
                          <li>Pick a value or variable</li>
                          <li>This time lets print the variable we made "myNumber" remember we set it to value 5</li>
                          </ol>
                          """
                              },
                    "code": {
                      "label": "💻 Blocks",
                      "content": """
                          <p>These small empty spots are called <b>slots</b>.</p>
                          <p>They work just like 👻 phantoms!</p>
                          """
                              },
                    "test": {
                      "label": "🧪 Check",
                      "content": """
                          <p>No empty spaces left? Your block is complete ✅</p>
                          """
                              },
                    "tip": {
                      "label": "💡 Tip",
                      "content": """
                          <p>If something looks unfinished, check for empty slots 👀</p>
                          """
                              }
                  }
                },

                {
                  "title": "✏️ Change a Block",
                  "tip":" ",
                  "tabs": {
                    "mission": {
                      "label": "🧠 Mission",
                      "content": """
                          <h3>Edit what you made.</h3>
                          <p>You will change a value inside a block.</p>
                          """
                              },
                    "build": {
                      "label": "🔧 Build",
                      "content": """
                          <ol>
                          <li>Click the number or value</li>
                          <li>Change it to something new</li>
                          <li>Lets change the value of myNumber to 10 using setvar</li>
                          </ol>
                          """
                              },
                    "code": {
                      "label": "💻 Blocks",
                      "content": """
                          <p>You don’t need to delete blocks to fix them 👍</p>
                          <p>Just click and change!</p>
                          """
                              },
                    "test": {
                      "label": "🧪 Check",
                      "content": """
                          <p>Did the number change? Nice! 🎉</p>
                          """
                              },
                    "tip": {
                      "label": "💡 Tip",
                      "content": """
                          <p>If it won’t change, click the value again slowly.</p>
                          """
                              }
                  }
                },

                {
                  "title": "📂 Try Another Section",
                  "tip":" ",
                  "tabs": {
                    "mission": {
                      "label": "🧠 Mission",
                      "content": """
                          <h3>Work in a new area.</h3>
                          <p>You will add a block in <b>Loop</b>.</p>
                          """
                              },
                    "build": {
                      "label": "🔧 Build",
                      "content": """
                          <ol>
                          <li>Open the <b>Loop</b> section 🔁</li>
                          <li>Click a 👻 phantom</li>
                          <li>Add a block</li>
                          <li>Lets make a line that will Print myNumber using serialprint</li>
                          </ol>
                          """
                              },
                    "code": {
                      "label": "💻 Blocks",
                      "content": """
                          <p>Different blocks belong in different sections.</p>
                          <p>The palette helps you choose the right one 👍</p>
                          """
                              },
                    "test": {
                      "label": "🧪 Check",
                      "content": """
                          <p>Is your block inside Loop? Perfect ✅</p>
                          """
                              },
                    "tip": {
                      "label": "💡 Tip",
                      "content": """
                          <p>If the wrong blocks show up, check which section you clicked.</p>
                          """
                              }
                  }
                },
               {
                  "title": "🏁 You Did It! Upload Your Code",
                  "tabs": {
                    "mission": {
                      "label": "🧠 Mission",
                      "content": """
                <h3>Time to run your program!</h3>
                <p>You built your code 🎉 Now let’s send it to your Arduino.</p>
                """
                    },
                    "build": {
                      "label": "🔧 Upload",
                      "content": """
                          <ol>
                          <li>Plug your Arduino into your computer 🔌</li>
                          <li>Start the <b>Arduino Agent</b> software</li>
                          <li>Click <b>Refresh</b> in the top left</li>
                          <li>Select your board from the dropdown</li>
                          <li>Click <b>Upload</b> 🚀</li>
                          </ol>
                          """
                    },
                    "code": {
                      "label": "💻 How It Works",
                      "content": """
                          <p>Your blocks turn into real Arduino code 💻</p>
                          <p>If your code is correct, it will upload to your board automatically.</p>
                          <p>You can also copy your code into the Arduino IDE, but we use the webpage here 👍</p>
                          """
                    },
                    "test": {
                      "label": "🧪 Check",
                      "content": """
                          <p>Click the <b>Serial Monitor</b> button 📟</p>
                          <p>You should see your message showing up!</p>
                          """
                    },
                    "tip": {
                      "label": "💡 Tips & Help",
                      "content": """
                          <p><b>🟢 If the Arduino Agent is running:</b></p>
                          <ul>
                          <li>You will see your board in the dropdown ✅</li>
                          <li>You are ready to upload 🚀</li>
                          </ul>

                          <p><b>🔴 If the Arduino Agent is NOT running:</b></p>
                          <ul>
                          <li>No boards will appear ❌</li>
                          <li>The upload will not work</li>
                          </ul>

                          <p><b>Fix it:</b></p>
                          <ul>
                          <li>Start the Arduino Agent</li>
                          <li>Click <b>Refresh</b> again 🔄</li>
                          </ul>

                          <p>Still not working?</p>
                          <ul>
                          <li>Check your USB cable 🔌</li>
                          <li>Try another port</li>
                          </ul>
                          """
                    }
                  }
                }
  
 ],
}

SKETCH_PRESET = {
    'sketch': """
//>> Step 1 - The Program Structure | open | blocks | filter | fill:false
void setup() {
}
void loop() {
}

//>> Step 2 - Start Communication | free | blocks | filter| fill:false
//?? Create a number variable
int myNumber = 5;

void setup() {
}
void loop() {
}

//>> Step 3 - Send Your First Message | guided | blocks | filter | fill:false
void setup() {
  //?? Setup the connection
  Serial.begin(9600);
  //?? Send a message to the computer
  Serial.println("Hello!");
}
void loop() {
}

//>> Step 4 - Print the Variable | guided | blocks | filter | fill:false

void setup() {
  //## Serial.begin(9600);
  //?? Print the variable value
  Serial.println(myNumber);
}
void loop() {
}

//>> Step 5 - Change the Variable | guided | blocks | filter | fill:false
void setup() {
  //## Serial.begin(9600);
  //?? Change the variable value
  myNumber = 10;
  //## Serial.println(myNumber);
}
void loop() {
}

//>> Step 6 - Move to Loop | guided | blocks | filter | fill:false

void loop() {
  //?? Print the variable repeatedly
  Serial.println(myNumber);
}

//>> Step 7 - Add a Delay | guided | blocks | filter | fill:false

void loop() {
  //## Serial.println(myNumber);
  //?? Wait 1 second between prints
  delay(1000);
}

//>> Step 8 - Tutorial Complete | open | blocks | filter |fill:false

void loop() {
  //## Serial.println(myNumber);
  //## delay(1000);
}
""",
}

CHALLENGE_PRESET = {
    'sketch': '...',
    'default_view': 'editor',
}

# Optional — progression sketch for guided block builder projects
PROGRESSION_PRESET = {
    'sketch': '...',  # contains //>> markers
}
PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
        "challenge": CHALLENGE_PRESET,
        "progression": PROGRESSION_PRESET,
    }
}