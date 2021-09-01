<?php
/**
 * Predmet: IPP 2021
 * Popis: Projekt c.2 - Testovaci ramec
 * Nazov suboru: test.php
 * Autor: Tomas Zatko (xzatko02)
 * Datum: 4.3.2021
 */
global $argc;
global $counter_all_tests;
global $counter_all_passed_tests;
global $counter_all_failed_tests;

$counter_all_tests = 0;	# pre spocitanie testov vo vsetkych testovanych adresaroch
$counter_all_passed_tests = 0;	# pre spocitanie uspesnych testov vo vsetkych testovanych adresaroch
$counter_all_failed_tests = 0;	# pre spocitanie neuspesnych testov vo vsetkych testovanych adresaroch
$mozne_argumenty_set = array("help", "directory:", "recursive", "parse-script:", "int-script:", "parse-only", "int-only", "jexamxml:", "jexamcfg:");
$mozne_argumenty = getopt(null, $mozne_argumenty_set);

# zistenie directory path pre vypis do html
if(array_key_exists("directory", $mozne_argumenty)) {
	$dir_path = $mozne_argumenty["directory"];
	#echo $dir_path;		# DEBUG VYMAZAT 
}
	if(array_key_exists("help", $mozne_argumenty)) {	// kontrola ci zadana polozka existuje v danom poli
	if($argc == 2) {	// zadany jeden argument
			fprintf(STDOUT, "Skript urceny na automaticke otestovanie aplikacie parse.php a interpret.py\n");
			fprintf(STDOUT, "Skript prejde zadany adresar s testami a vyuzije ich pre automaticke otestovanie spravnej funkcnosti\n");
			fprintf(STDOUT, "jedneho alebo oboch predchadzajucich skriptov vratene generovania prehladneho suhrnu v HTML 5 na STDOUT.\n");
			fprintf(STDOUT, "\n--help................zobrazi napovedu\n");
			fprintf(STDOUT, "--directory PATH......testy bude hladat v zadanom adresari, ak nezadany - pracuje sa s cwd\n");
			fprintf(STDOUT, "--recursive.......... testy budu hladane v cwd a zaroven vo vsetkych podadresaroch\n");
			fprintf(STDOUT, "--parse-script FILE...subor so skriptom pre analyzu zdroj.kodu v IPPcode21, ak nezadany - pracuje sa s parse.php v aktualnom adresari\n");
			fprintf(STDOUT, "--int-script FILE.....subor so skriptom pre interpret XML reprezentacie kodu v IPPcode21, ak nezadany - pracuje sa s interpret.py v aktualnom adresari\n");
			fprintf(STDOUT, "--parse-only..........bude testovany len skript pre analyzu zdroj.kodu v IPPcode21, vystup porovnavany s nastrojom A7Soft JExamXML\n");
			fprintf(STDOUT, "--int-only............bude testovany len skript pre interpret XML reprezentacie kodu v IPPcode21\n");
			fprintf(STDOUT, "--jexamxml FILE.......subor s JAR balickom s nastrojom A7Soft JExamXML, ak nezadany - uvazuje sa umiestnenie na serveri Merlin\n");
			fprintf(STDOUT, "--jexamcfg FILE.......subor s konfiguraciou nastroja A7Soft JExamXML, ak nezadany - uvazuje sa umiestnenie na serveri Merlin\n");
			exit(0);
		} else {
			fprintf(STDOUT, "Parameter --help nie je mozne kombinovat so ziadnym dalsim parametrom!\n");
			exit(10);	
		}
	}

?>

<!DOCTYPE HTML>
<html lang="sk">
	<head>
		<meta charset="utf-8" />
		<style>
		body
		{
			background-color: #FFF;
			margin: 0px;
		}
		
		h1
		{
			font-size: 25px;
			font-family: Consolas,monospace;
		}
		
		.header
		{
			background-color: #3ABBEE;
			text-align: left;
			padding: 0.05px;
		}
		html {
			height: 100%;
		}
		body {
			background-image: linear-gradient(to left, #FFFFFF, #C7CACB);
		}
		.folder
		{
			background-color: #ffffff;
			padding: 5px;
		}
	
		</style>
		<title>IPP </title>
	</head>
	<body>
		<div class="header">
			<h1> <p style="color:white"> IPP - Tests Results </p> </h1>
		</div>
		<div class="text">
			<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 15px; padding-right:40px;"> Predmet: IPP<br>Projekt: test.php<br>Login: xzatko02<br></p>
			<p style="color:#585E60; text-align:left;font-family: Consolas,monospace; font-size: 30px; padding-left:40px;"> <?php if($rekurzia == false){echo ('Folder "'.$dir_path.'"');} else {echo ('');} ?> </p>
		</div>
		<p style="color:#585E60; font-family: Consolas,monospace; font-size: 30px;">
			<div class="folder">
				<div style="float: left; padding-left:40px; color:#585E60; font-family: Consolas,monospace; font-size: 30px;"><?php echo ('File'); ?></div>
                <div style="float: right; padding-right:40px; color:#585E60; font-family: Consolas,monospace; font-size: 30px;"><?php echo ('Result'); ?></div>
                <div style="margin: 0 auto; width: 700px; color:#585E60; font-family: Consolas,monospace; font-size: 30px;"><?php echo ('Parse.php')?>&emsp; &emsp; &emsp; &emsp; &emsp; &emsp;<?php echo('Interpret.py'); ?></div>		
			</div>
		</p>	
		<div class="tests_results">
			<?php auto_tests($dir_path); ?>
		</div>
		<div class="text">
			<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 18px; padding-right:40px;margin: 0px;"> <b><?php echo ('All Tests: '.$counter_all_tests);?> </b> </p>
			<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 18px; padding-right:40px;margin: 0px;"> <b><?php echo ('All Passed Tests: '.$counter_all_passed_tests);?> </b> </p>
			<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 18px; padding-right:40px;margin: 0px;"> <b><?php echo ('All Failed Tests: '.$counter_all_failed_tests);?> </b> </p>
		</div>
	</body>
</html>

<?php

exit(0);								// uspesne ukoncenie programu

function auto_tests($dir_path){
	
	global $argc;
	global $counter_all_tests;	# pre spocitanie testov vo vsetkych testovanych adresaroch
	global $counter_all_passed_tests;	# pre spocitanie uspesnych testov vo vsetkych testovanych adresaroch
	global $counter_all_failed_tests;	# pre spocitanie neuspesnych testov vo vsetkych testovanych adresaroch
	$mozne_argumenty_set = array("help", "directory:", "recursive", "parse-script:", "int-script:", "parse-only", "int-only", "jexamxml:", "jexamcfg:");
	$mozne_argumenty = getopt(null, $mozne_argumenty_set);
	$tests_counter = 0;			# pocitadlo testov (*.src) pre zobrazenie v html
	$counter_src_tests = 0;	# pocitadlo testov (*.src) pre zobrazenie v html, pre porovanie aby som vedel, kedy vypisat dany pocet do html (po poslednom subore)
	$pass_tests = 0;			# pocitadlo uspesnych testov 
	$fail_tests = 0;			# pocitadlo neuspesnych testov
	$only_once = 0;				# priznak na jedineho vypisania nazvu adresy do html
	$rekurzia = false;			# priznak vykonania rekurzie
	$parse = 'parse.php';		# pociatocny nazov skriptu parse.php (mozna zmena kvoli argumentu --parse-script)
	$interpret = 'interpret.py';# pociatocny nazov skriptu interpret.py (mozna zmena kvoli argumentu --int-script)
	$jump_to_end = false;
	$jexamXML = '/pub/courses/ipp/jexamxml/jexamxml.jar';
	$jexamXMLcfg = '/pub/courses/ipp/jexamxml/options';
	

	if((array_key_exists("int-only", $mozne_argumenty)) and (array_key_exists("parse-only", $mozne_argumenty))) {
		fprintf(STDERR, "Cannot be combined int-only and parse-only.\n");
		exit(10); 
	}
	
	if((array_key_exists("int-script", $mozne_argumenty)) and (array_key_exists("parse-only", $mozne_argumenty))) {
		fprintf(STDERR, "Cannot be combined int-script and parse-only.\n");
		exit(10); 
	}

	if(array_key_exists("recursive", $mozne_argumenty)) {
		$rekurzia = true;	// nastavenie priznaku, ze sa budu prehladavat aj vsetky podadresare
	}	

	# zistenie cwd path, pokial nie je zadany ako parameter
	if(!array_key_exists("directory", $mozne_argumenty)) {
		$dir_path = getcwd();
		#echo $dir_path ;		# DEBUG VYMAZAT 
	}

	# kontrola, ci zadany adresar existuje
	if(file_exists($dir_path)){
		;
	}
	else{
		fprintf(STDERR, "Directory path does not exist.\n");
		exit(41);
	}
	
	# pripadne nastavenie cesty skriptu parse.php
	if(array_key_exists("parse-script", $mozne_argumenty)) {
		$parse = $mozne_argumenty["parse-script"];
	}	
	
	# pripadne nastavenie cesty skriptu interpret.py
	if(array_key_exists("int-script", $mozne_argumenty)) {
		$interpret = $mozne_argumenty["int-script"];
	}	
	
	# testuje sa len scriptom parse.php (bez interpret.py)
	if(array_key_exists("parse-only", $mozne_argumenty)) {
		$parse_only = true;
	}	
	
	# ak je zadany --jexamxml=file, tak nastavujem na novu cestu
	if(array_key_exists("jexamxml", $mozne_argumenty)) {
		$jexamXML = $mozne_argumenty["jexamxml"];
	}
	
	# ak je zadany --jexamcfg=file , tak nastavujem na novu cestu
	if(array_key_exists("jexamcfg", $mozne_argumenty)) {
		$jexamXMLcfg = $mozne_argumenty["jexamcfg"];
	}

	# skenovanie adresara a ukladanie test paths
	$tests_filenames = scandir($dir_path);
	
	$rec_dir = $dir_path.'/';	# pre rekurzivne predavanie adresy

	foreach($tests_filenames as $test_file_name){
		if(preg_match("/.src$/", $test_file_name)){
			$counter_src_tests = $counter_src_tests + 1;
		}
		
	}
			
	# cyklom prechadzam cez vsetky prvky pola, kde su ulozene nazvy suborov a vytvaram neexistujuce subory s priponami .rc, .out, .in
	# nasledne porovnavam .rc, .out a .in subory a vytvaram html
	foreach($tests_filenames as $test_file_name){
		
		if(preg_match("/.src$/", $test_file_name)){
			
			# jediny vypis adresy do html
			$only_once = $only_once + 1;
			if($only_once == 1){
				?>
				<div class="text">
					<p style="color:#585E60; text-align:left;font-family: Consolas,monospace; font-size: 30px; padding-left:40px;"> <?php echo ('Folder "'.$rec_dir.'"');?> </p>
				</div>
				<?php
			}
			
			# navysenie poctu testov v danej zlozke
			$tests_counter = $tests_counter + 1;
			
			# od src suboru odstranim priponu, "add.src" -> "add"
			$test_file_name_cut = substr($test_file_name, 0, strrpos( $test_file_name, '.'));
			
			# idem hladat subor s PATH a s priponou .rc (ktoru pridam) a povodnym src nazvom pre pomenovanie novo vytvoreneho suboru v pripade neexistencie
			$test_file_name_rc = $dir_path."/".$test_file_name_cut.".rc";
			$test_file_name_out = $dir_path."/".$test_file_name_cut.".out";
			$test_file_name_in = $dir_path."/".$test_file_name_cut.".in";
			
			# pokial subor rc neexistuje, vygenerujem ho ako subor s hodnotou: 0
			if(!file_exists($test_file_name_rc)){
				$new_rc_file = fopen($test_file_name_rc, "w");
				$content = "0";
				fwrite($new_rc_file, $content);
				fclose($new_rc_file);
			}
			
			# pokial subor out neexistuje, vygenerujem ho ako prazdny subor
			if(!file_exists($test_file_name_out)){
				$new_out_file = fopen($test_file_name_out, "w");
				fclose($new_out_file);
			}
			
			# pokial subor in neexistuje, vygenerujem ho ako prazdny subor
			if(!file_exists($test_file_name_in)){
				$new_in_file = fopen($test_file_name_in, "w");
				fclose($new_in_file);
			}
		}
		# ak subor nie je s priponou *.src, prejdi na dalsi subor
		else{
			continue;
		}
		
		# vykonanie skriptu parse.php
		$test_file_name_src = $dir_path."/".$test_file_name_cut.".src";
		
		# nevykona sa skript parse.php, pokial --int-only
		if(!array_key_exists("int-only", $mozne_argumenty)){
			exec("php7.4 $parse <\"$test_file_name_src\" >\"$test_file_name_cut.parse.out\"", $dump, $parse_ret_code);	# DOPISAT PHP7.4 pre Merlina
		}
		
		# vykonanie skriptu python.py, len ak nie je --parse-only
		if(!array_key_exists("parse-only", $mozne_argumenty) and !array_key_exists("int-only", $mozne_argumenty)) {
			exec("python3.8 $interpret --source=\"$test_file_name_cut.parse.out\" --input=\"$test_file_name_in\" >\"$test_file_name_cut.interpret.out\"", $dump, $interpret_ret_code); 	# DOPISAT PYTHON3.8 pre Merlina
		}
		
		# vykonanie skriptu python.py, len ak je --int-only
		if(array_key_exists("int-only", $mozne_argumenty)) {
			exec("python3.8 $interpret --source=\"$test_file_name_src\" >\"$test_file_name_cut.interpret.out\"", $dump, $interpret_ret_code); 	# DOPISAT PYTHON3.8 pre Merlina
		}
		
		# nacitanie referencneho return code zo suboru
		$file = fopen($test_file_name_rc, "r");
		$interpret_ref_ret_code = fgets($file);
		fclose($file);

		# --PARSE-ONLY: porovnam return code z parse.php a referencny return code *.rc suboru
		if(array_key_exists("parse-only", $mozne_argumenty)) {	
			if($parse_ret_code != $interpret_ref_ret_code){	# zo suboru *rc (pomenovanie interpret je pri --parse-only irelevantne)
				$result = 'failed';
				$parse_ref_ret_code = $interpret_ref_ret_code;
				$fail_tests = $fail_tests + 1;
			}
			elseif($parse_ret_code != 0 and $interpret_ref_ret_code != 0 and $parse_ret_code == $interpret_ref_ret_code){
				$result = 'passed';
				$parse_ref_ret_code = $parse_ret_code;
				$pass_tests = $pass_tests + 1;
			}
			elseif($parse_ret_code == 0 and $interpret_ref_ret_code == 0){
				$parse_ref_ret_code = $parse_ret_code;
				# porovnanie xml *.out suborov pomocou JExamXML
				exec("java -jar jexamxml.jar \"$test_file_name_cut.parse.out\" \"$test_file_name_out\" \"$jexamXMLcfg\"", $trash, $diff_xml);
				if($diff_xml == 0){
					$result = 'passed';
					$pass_tests = $pass_tests + 1;
				}
				elseif($diff_xml == 1){
					$result = 'outputs not equal';
					$fail_tests = $fail_tests + 1;
				}
				else{
					$result = 'undefined';
					$fail_tests = $fail_tests + 1;
				}
				
			}
			$interpret_ref_ret_code = '-';	# aby sa nevypisal kod z interpretacie do html
			$interpret_ret_code = '-';
		}
		
		# --INT-ONLY: porovnam return code z interpret.py a referencny return code *.rc suboru
		if(array_key_exists("int-only", $mozne_argumenty)) {	
			if($interpret_ret_code != $interpret_ref_ret_code){
				$result = 'failed';
				$fail_tests = $fail_tests + 1;
			}
			elseif($interpret_ret_code != 0 and $interpret_ref_ret_code != 0 and $interpret_ret_code == $interpret_ref_ret_code){
				$result = 'passed';
				$pass_tests = $pass_tests + 1;
			}
			elseif($interpret_ret_code == 0 and $interpret_ref_ret_code == 0){
				# porovnanie *.out suborov pomocou diff
				exec("diff -q \"$test_file_name_out\" \"$test_file_name_cut.interpret.out\"", $trash, $diff_out);
				if($diff_out == 0){
					$result = 'passed';
					$pass_tests = $pass_tests + 1;
				}
				elseif($diff_out == 1){
					$result = 'outputs not equal';
					$fail_tests = $fail_tests + 1;
				}
				else{
					$result = 'undefined';
					$fail_tests = $fail_tests + 1;
				}
				
			}
			$parse_ref_ret_code = '-';	# aby sa nevypisal kod z parseru do html
			$parse_ret_code = '-';
		}
		
		# preskoc, ked --parse-only or --int-only
		if(!array_key_exists("parse-only", $mozne_argumenty) and !array_key_exists("int-only", $mozne_argumenty)) {
			# porovnavam navrateny recturn code z parse.php a return code z *rc suboru, ci neobsahuje 21-23 (chyby analyzy) - ak ano - nevykonavam interpretaciu a ukoncujem testovanie
			if(($parse_ret_code == 21 and $interpret_ref_ret_code == 21) or ($parse_ret_code == 22 and $interpret_ref_ret_code == 22) or ($parse_ret_code == 23 and $interpret_ref_ret_code == 23)){
				$pass_tests = $pass_tests + 1;	# pocitadlo uspesnych testov
				$interpret_ref_ret_code = '-';	# aby sa nevypisal kod z interpretacie do html
				$interpret_ret_code = '-';
				$parse_ref_ret_code = $parse_ret_code;
			}
			# ak analyza posle chybovy return code a nerovna sa return codu z *rc suboru - test failed
			elseif(($parse_ret_code == 21 and $interpret_ref_ret_code != $parse_ret_code) or ($parse_ret_code == 22 and $interpret_ref_ret_code != $parse_ret_code) or ($parse_ret_code == 23 and $interpret_ref_ret_code != $parse_ret_code)){
				$fail_tests = $fail_tests + 1;	# pocitadlo neuspesnych testov
				$parse_ref_ret_code = $interpret_ref_ret_code;
				$interpret_ref_ret_code = '-';	# aby sa nevypisal kod z interpretacie do html
				$interpret_ret_code = '-';	
			}
			else{
				$parse_ref_ret_code = 0;
			}
			
			# analyza poslala chybovy return code - nevypisujem return codes interpretacie do html
			if($interpret_ref_ret_code == '-' and $interpret_ret_code == '-'){
				;
			}
			# porovnavam navrateny return code z interpret.py skriptu a referencny return code
			# obe sa rovnaju 0 alebo sa rovnaju ich hodnoty
			elseif($interpret_ref_ret_code == 0 and $interpret_ret_code == 0 or $interpret_ref_ret_code == $interpret_ret_code){
				#echo "ok"; # DEBUG
				$pass_tests = $pass_tests + 1;	# pocitadlo uspesnych testov
			}
			
			# rozdielne return codes - test nepresiel
			elseif($interpret_ref_ret_code != $interpret_ret_code){
				#echo "fail"; # DEBUG
				$fail_tests = $fail_tests + 1;	# pocitadlo neuspesnych testov
				$result = 'failed';
			}
		}
			
		# preskoc ak --parse-only
		if(!array_key_exists("parse-only", $mozne_argumenty)){
		# porovnavam referencny *.out subor a *.out, LEN V PRIPADE ak su oba subory *.rc s hodnotou: 0
			if(($interpret_ref_ret_code == 0 and $interpret_ret_code == 0) or ($interpret_ref_ret_code == $interpret_ret_code and $interpret_ref_ret_code != '-' and $interpret_ret_code != '-')){
				exec("diff -q \"$test_file_name_out\" \"$test_file_name_cut.interpret.out\"", $trash, $diff_out);
				if($diff_out == 0){
				#echo $diff_out; # DEBUG
				$result = 'passed';
				}
				else{
					;	# DOPLNIT AK RC CODES STEJNE ALE OUT ROZDIELNE - AKY VYSTUP V HTML????
				}
			}
		}
		
		# vymazanie vytvorenych docasnych (tmp) suborov v cwd (*tmp.in a *tmp.out)
		if(file_exists("$test_file_name_cut.parse.out")){
		unlink("$test_file_name_cut.parse.out");
		}
		if(file_exists("$test_file_name_cut.interpret.out")){
		unlink("$test_file_name_cut.interpret.out");
		}
?>		
<p style="color:#585E60; font-family: Consolas,monospace; font-size: 20px;">
	<div class="folder">
				<div style="float: left; padding-left:40px; color:#585E60; font-family: Consolas,monospace; font-size: 20px;"><?php echo ($test_file_name_cut); ?></div>
				<?php if($result == 'passed'){	# zelena farba slova passed
				?>
				<div style="float: right; padding-right:40px; color:#2ECC71; font-family: Consolas,monospace; font-size: 20px;"><?php echo ($result); ?></div>
				<?php
				}
				elseif($result == 'failed' or $result == 'outputs not equal' or $result == 'undefined'){	# cervena farba slova failed / outputs not equal / undefined
				?>
				<div style="float: right; padding-right:40px; color:#EC7063; font-family: Consolas,monospace; font-size: 20px;"><?php echo ($result); ?></div>
				<?php
				}
				?>
				<div style="margin: 0 auto; width: 700px; color:#585E60; font-family: Consolas,monospace; font-size: 20px;"><?php echo ('expected rc: '.$parse_ref_ret_code.' got: '.$parse_ret_code)?>&emsp; &emsp; &emsp;<?php echo(' expected rc: '.$interpret_ref_ret_code.' got: '.$interpret_ret_code); ?></div>		
	</div>
</p>			
<?php
		# vypis pocet testov do html
		if($counter_src_tests == $tests_counter){
			$counter_all_tests = $counter_all_tests + $counter_src_tests;
			$counter_all_passed_tests = $counter_all_passed_tests + $pass_tests;
			$counter_all_failed_tests = $counter_all_failed_tests + $fail_tests;
?>
			<div class="text">
				<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 18px; padding-right:40px;margin: 0px;"> <?php echo ('Total Tests: '.$tests_counter);?> </p>
				<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 18px; padding-right:40px;margin: 0px;"> <?php echo ('Passed Tests: '.$pass_tests);?> </p>
				<p style="color:#585E60; text-align:right;font-family: Consolas,monospace; font-size: 18px; padding-right:40px;margin: 0px;"> <?php echo ('Failed Tests: '.$fail_tests);?> </p>
			</div>
<?php
		}
		
	}
	
	# vykonavanie rekurzivneho vyhladavania adresarov a rekurzivneho volania
	foreach($tests_filenames as $test_file_name){
		if($rekurzia == true){
				$recursive = $rec_dir.$test_file_name;
				if($test_file_name == '..' or $test_file_name == '.'){
					continue;
				}
				if(is_dir($recursive)){
					#echo($recursive);
					auto_tests($recursive);	# rekurzivne volanie
				}
			}
	}
}
?>