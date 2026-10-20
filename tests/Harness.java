import com.ansub.tvhome.LocalTransferServer;
import java.io.*;
public class Harness {public static void main(String[] args)throws Exception{LocalTransferServer s=new LocalTransferServer(new File(args[0]),Long.parseLong(args[1]),message->{});System.out.println(s.port()+" "+s.token);System.out.flush();new BufferedReader(new InputStreamReader(System.in)).readLine();s.close();}}
