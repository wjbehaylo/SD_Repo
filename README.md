# SD_Repo
This is the repository for Colorado School of Mines senior design group 50: Variable Object Capture Mechanism. It will contain all of the code relevant to the project. To group members, please ask Walter (me) if you don't have experience working with Github. This README shall serve as a general introduction to the nature of the code and usage of the repo. 

#README
* PI_code: directory containing the code that will be run on the Raspberry Pi 5 embedded system.
* ARD_code: directory containing the control system code that will be run on the Arduino Uno 3. 

#Usage
Github is a very useful tool to manage a team's contributions to a library of code, as well as manage versions of the code to use when debugging. Please, as mentioned above, reach out to Walter if you have questions about how to use Github or the repo. Failure to do so could result in loss of work and progress, even corruption of the repository as a whole. README files are used as the documentation for a directory as a whole. If you create a new file, be sure to document it well, according to the 'documentation' section of this README.

#Documentation
Within each file containing code, at the top there should be an introduction with the following information.

READMEs
* Within each directory will be a README, defining the contents of the folder in some detail. This will be redundant, and the information contained within the parent directory will just be an abstracted overview of the information within the child directory's README.
* This can just be an overview of the file/folder's contents, or in more detail if necessary. This one is very detailed

Code file documentation
* Purpose: summary of the code application (be it for experimentation, prototyping, or deliverable).
* Contributors: Full information of authors and their respective contributions.
* Sources: any online documentation that code or inspiration for code is sourced from. Within reason (no need to cite documentation for 'print()'
* Relevant files: if this draws from other code, or other code draws from this, please cite the relevant file

Within the code, there should be extensive, almost unnecessary commenting. Generally try to include the author's thought process as the code is executing:
* When defining variables, include their application.
* Before any conditional statements (IF, OR, AND, XOR, etc), include the logic behind them
* Before loops: what is being counted? What is the point?
* Any user defined functions should be defined in terms of inputs, outputs, return values, and functionality
* If there is something that you find confusing when you're coding, and you figure it out, explain it so that the next person can avoid the same confusion.
* There is no such thing as too many comments, as long as they are all helpful in your opinion. We can clean up the comments on our final submitted code if necessary. 

