const int StepX = 2;
const int DirX = 5;
void setup() {
  pinMode(StepX,OUTPUT);
  pinMode(DirX,OUTPUT);
}

void loop() {
 digitalWrite(DirX, HIGH); // set direction, HIGH for clockwise, LOW for anticlockwise

 
 for(int x = 0; x<200; x++) { // loop for 200 steps
  digitalWrite(StepX,HIGH);
  delayMicroseconds(500);
  digitalWrite(StepX,LOW); 
  delayMicroseconds(500);
 }
delay(1000); // delay for 1 second
digitalWrite(DirX, LOW);
 for(int x = 0; x<200; x++) { // loop for 200 steps
  digitalWrite(StepX,HIGH);
  delayMicroseconds(500);
  digitalWrite(StepX,LOW); 
  delayMicroseconds(500);
 }
delay(1000); // delay for 1 second
}