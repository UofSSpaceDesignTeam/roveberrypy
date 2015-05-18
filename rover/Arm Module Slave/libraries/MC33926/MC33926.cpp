#include "Arduino.h"
#include "MC33926.h"

MC33926::MC33926(int in1, int in2)
{
	motorA = in1;
	motorB = in2;
	pinMode(motorA, OUTPUT);
	pinMode(motorB, OUTPUT);
	digitalWrite(motorA, LOW);
	digitalWrite(motorB, LOW);
	count = 0;
}

void MC33926::set(int val)
{
	val = constrain(val, -255, 255);
	if(val == 0)
	{
		digitalWrite(motorA, LOW);
		digitalWrite(motorB, LOW);
	}
	else if(val > 0)
	{
		analogWrite(motorA, val);
		digitalWrite(motorB, LOW);
	}
	else
	{
		digitalWrite(motorA, LOW);
		analogWrite(motorB, abs(val));
	}
}

void MC33926::addToCount(int num)
{
	count += num;
}

int MC33926::getCount()
{
	return count;
}

