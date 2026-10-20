import com.ansub.tvhome.ThumbnailCatalog;
import java.io.*;
import java.nio.charset.StandardCharsets;
public class CatalogTests{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args)throws Exception{
  String html="<a href=\"Super%20Mario%20Kart%20(USA).png\">a</a>\n<a href=\"Super%20Mario%20Kart%20(Japan).png\">b</a>\n<a href=\"Castlevania%20-%20Symphony%20of%20the%20Night%20(USA).png\">c</a>\n<a href=\"Castlevania%20Chronicles%20(USA).png\">d</a>\n<a href=\"Super%20Bomberman%205%20(Japan).png\">e</a>\n<a href=\"..%2Fescape.png\">bad</a>\n<a href=\"https%3A%2F%2Fevil.example%2Fx.png\">bad</a>";
  ThumbnailCatalog c=ThumbnailCatalog.parse(new ByteArrayInputStream(html.getBytes(StandardCharsets.UTF_8)));
  check(ThumbnailCatalog.candidate("Super Bomberman 5 Gold Cartridge (J) [!].smc").equals("Super Bomberman 5 (Japan).png"));check(ThumbnailCatalog.candidate("Super Mario World (U) [!].smc").equals("Super Mario World (USA).png"));check(c.size()==4);check(c.find("Super Mario Kart (U) [!].smc").contains("USA"));check(c.find("Super Mario Kart (Japan).sfc").contains("Japan"));check(c.find("Castlevania.chd")==null);check(c.find("Castlevania - Symphony of the Night.chd").contains("Symphony"));check(c.find("Super Bomberman 5 Gold Cartridge (J) [!].smc").contains("Bomberman 5"));check(c.find("Unknown.sfc")==null);check(c.find("escape.sfc")==null);check(ThumbnailCatalog.encode("A+B & C.png").equals("A%2BB%20%26%20C.png"));check(ThumbnailCatalog.normalize("Donkey Kong Country (U) (V1.2) [!].smc").equals("donkey kong country"));
  boolean rejected=false;try{ThumbnailCatalog.base("../invalid");}catch(IllegalArgumentException e){rejected=true;}check(rejected);
  try{ThumbnailCatalog.parse(new ByteArrayInputStream("no index".getBytes(StandardCharsets.UTF_8)));throw new AssertionError();}catch(IOException expected){}
  System.out.println("Matcher: regiões, tags, edição, ambiguidade, ausência, escape de URL e caminhos rejeitados OK.");
 }
}
