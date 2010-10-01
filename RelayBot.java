import java.awt.AWTException;
import java.awt.Robot;
import java.awt.event.InputEvent;
import java.io.*;
import java.net.*;

public final class RelayBot
{
    public static void main(String[] args) throws AWTException
    {
    Robot robot = new Robot();

    robot.setAutoDelay(5);
    robot.setAutoWaitForIdle(true);
	int mx;
	int my;
	mx = 0;
	my = 0;

	String userInput;
	BufferedReader stdIn = new BufferedReader(
											  new InputStreamReader(System.in));

	try {
		while ((userInput = stdIn.readLine()) != null) {
			int d = 0;
			try {
				d = Integer.parseInt(userInput.substring(2));
			}
			catch(java.lang.NumberFormatException e){
				//System.out.println("got bad value: " + userInput);
			}
			//System.out.println(userInput);

			switch(userInput.charAt(0)) {
			case 'q':
				System.exit(0);
				break;
			case 'm':
				switch(userInput.charAt(1)) {
				case 'x':
					mx = d;
					break;
				case 'y':
					my = d;
					break;
				case 'w':
					robot.mouseWheel(d);
					break;
				}
				break;
			case 'k':
				int key=0;
				switch(d) {
				case 1001:
					key = InputEvent.BUTTON1_MASK;
				case 1002:
					if(key == 0)//Hackish way to only set key once
						key = InputEvent.BUTTON3_MASK;
				case 1003:
					if(key == 0)
						key = InputEvent.BUTTON2_MASK;
					//System.out.print("got mouse event key = ");
					//System.out.println(key);
					switch(userInput.charAt(1)) {
					case 'p':
						robot.mousePress(key);
						//System.out.println("got mouse press");
						break;
					case 'r':
						robot.mouseRelease(key);
						//System.out.println("got mouse release");
						break;
					}
					break;
				default:
					key = d;
					switch(userInput.charAt(1)) {
					case 'p':
						robot.keyPress(key);
						break;
					case 'r':
						robot.keyRelease(key);
						break;
					}
				}
			}
			robot.mouseMove(mx, my);
		}
	} catch (IOException e) {
		System.err.println("Couldn't get I/O for "
						   + "the connection to: taranis.");
		System.exit(1);
	}


    System.exit(0);
    }
}

