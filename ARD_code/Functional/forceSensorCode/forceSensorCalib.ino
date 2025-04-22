void testForceReadings() {
  Serial.println("Force Reading Test");
  Serial.println("Analog\tVoltage\tForce(N)");
  for(int i=0; i<1024; i+=100) {
    float voltage = (i/1023.0)*5.0;
    float force = 1.0 + ((voltage-1.67)/(3.33-1.67))*2.0;
    Serial.print(i); Serial.print("\t");
    Serial.print(voltage,2); Serial.print("\t");
    Serial.println(force,2);
  }
}