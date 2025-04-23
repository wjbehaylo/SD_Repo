/* 
Force sensor reading code

Senses the amount of force applied to the linear soft pot reading by reading out an analog voltage
Reads up to 3N of Force
Example sketch for SparkFun's soft membrane potentiometer
  (https://www.sparkfun.com/products/8680)

- Connect the softpot's outside pins to 5V and GND (the outer pin with an arrow
indicator should be connected to GND). 
- Connect the middle pin to A0.

As the voltage output of the softpot changes, a line graph printed to the
serial monitor should match the wiper's position.

Development environment specifics:
Arduino 1.6.7
******************************************************************************/
// const int SOFT_POT_PIN0 = A4; // Pin connected to softpot wiper FORCE SENSOR NOT WORKING
const int SOFT_POT_PIN1 = A1; // Pin connected to softpot wiper
const int SOFT_POT_PIN2 = A2; // Pin connected to softpot wiper
const int SOFT_POT_PIN3 = A3; // Pin connected to softpot wiper


const int GRAPH_LENGTH = 40; // Length of line graph

void setup() 
{
  Serial.begin(9600);
  // pinMode(SOFT_POT_PIN0, INPUT);
  pinMode(SOFT_POT_PIN1, INPUT);
  pinMode(SOFT_POT_PIN2, INPUT);
  pinMode(SOFT_POT_PIN3, INPUT);
}

void loop() 
{
  // Read in the soft pot's ADC value
  // int softPotADC0 = analogRead(SOFT_POT_PIN0);
  int softPotADC1 = analogRead(SOFT_POT_PIN1);
  int softPotADC2 = analogRead(SOFT_POT_PIN2);
  int softPotADC3 = analogRead(SOFT_POT_PIN3);

  // Map the 0-1023 value to 0-40
  // int softPotPosition = map(softPotADC, 0, 1023, 0, GRAPH_LENGTH);

  // Print a line graph:
  // Serial.print("<"); // Starting end
  // for (int i=0; i<GRAPH_LENGTH; i++)
  // {
  //   if (i == softPotPosition) Serial.print("|");
  //   else Serial.print("-");
  // }
  // Serial.println("> (" + String(softPotADC) + ")");

  // if (softPotADC0 > 10) { // noise
  //   Serial.println("0: " + String(softPotADC0));
  // }
  if (softPotADC1 > 10) {
    Serial.println("1: " + String(softPotADC1));
  }
  if (softPotADC2 > 10) {
    Serial.println("2: " + String(softPotADC2));
  }
  if (softPotADC3 > 10) {
    Serial.println("3: " + String(softPotADC3));
  }

  delay(1000);
}