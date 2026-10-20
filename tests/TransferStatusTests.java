import com.ansub.tvhome.LocalTransferServer;
import java.io.*;
import java.net.*;
public class TransferStatusTests {
 private static void check(Throwable t,int expected){int actual=LocalTransferServer.statusFor(t);if(actual!=expected)throw new AssertionError(t+": "+actual+" != "+expected);}
 public static void main(String[] args){check(new SocketTimeoutException(),408);check(new EOFException(),400);check(new IOException("Envio interrompido"),400);check(new SocketException("Connection reset"),400);check(new URISyntaxException("private","invalid"),400);check(new NumberFormatException(),400);check(new IllegalArgumentException(),400);check(new IOException("A reserva de espaço livre foi atingida"),507);check(new IOException("disk",new IOException("ENOSPC")),507);check(new IOException("No space left on device"),507);check(new IOException("private path"),500);check(new Exception("private"),500);System.out.println("statusFor: 12 cenários passaram.");}
}
