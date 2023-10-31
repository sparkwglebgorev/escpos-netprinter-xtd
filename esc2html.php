<?php
/**
 * Utility to convert binary ESC/POS data to HTML
 */
require_once __DIR__ . '/vendor/autoload.php';

use ReceiptPrintHq\EscposTools\Parser\Context\Code2DStateStorage;
use ReceiptPrintHq\EscposTools\Parser\Parser;
use ReceiptPrintHq\EscposTools\Parser\Context\InlineFormatting;

$debugMode = false;
$targetFilename = "";

error_log("esc2html starting", 0);
// Usage
if ($argc < 2) {
    print("Usage: " . $argv[0] . " [--debug] filename \n"."zéro args");
    die();
}
else {
    if ($argv[1]=='--debug'){ 
        $debugMode = true;
        if (!isset($argv[2])) {
            print("Usage: " . $argv[0] . " [--debug] filename ". $argc-1 . " arguments received\n");
            die();
        }
        else $targetFilename = $argv[2];
        error_log("Debug mode enabled", 0);
    }
    else {  //First argument is not '--debug'
        if(isset($argv[2])) { // But there is at least 2 args
            print("Usage: " . $argv[0] . " [--debug] filename \n". $argc-1 . " arguments received\n");
            die();
        }
        else $targetFilename = $argv[1]; //The only argument is the filename.
    }
}
error_log("Target filename: " . $targetFilename . "", 0);

// Load in a file
$fp = fopen($targetFilename, 'rb');

$parser = new Parser();
$parser -> addFile($fp);

// Extract text
$commands = $parser -> getCommands();
$formatting = InlineFormatting::getDefault();
$outp = array();
$lineHtml = "";
$bufferedImg = null;
$imgNo = 0;
$skipLineBreak = false;
$code2dStorage = new Code2DStateStorage();

foreach ($commands as $cmd) {
    if ($debugMode) error_log("". get_class($cmd) ."", 0); //Output the command class in the debug console

    if ($cmd -> isAvailableAs('InitializeCmd')) {
        $formatting = InlineFormatting::getDefault();
    }
    if ($cmd -> isAvailableAs('InlineFormattingCmd')) {
        $cmd -> applyToInlineFormatting($formatting);
    }
    if ($cmd -> isAvailableAs('TextContainer')) {
        // Add text to line
        // TODO could decode text properly from legacy code page to UTF-8 here.
        #if ($debugMode) error_log("Text or unidentified command: '". $cmd->get_data() ."' ", 0);
        $spanContentText = $cmd -> getText();
        $lineHtml .= span($formatting, $spanContentText);
    }
    if ($cmd -> isAvailableAs('LineBreak') && $skipLineBreak) {
        $skipLineBreak = false;
    } else if ($cmd -> isAvailableAs('LineBreak')) {
        // Write fresh block element out to HTML
        if ($lineHtml === "") {
            $lineHtml = span($formatting);
        }
        // Block-level formatting such as text justification
        $classes = getBlockClasses($formatting);
        $classesStr = implode(" ", $classes);
        $outp[] = wrapInline("<div class=\"$classesStr\">", "</div>", $lineHtml);
        $lineHtml = "";
    }
    if ($cmd -> isAvailableAs('GraphicsDataCmd') || $cmd -> isAvailableAs('GraphicsLargeDataCmd')) {
        $sub = $cmd -> subCommand();
        if ($sub -> isAvailableAs('StoreRasterFmtDataToPrintBufferGraphicsSubCmd')) {
            $bufferedImg = $sub;
        } else if ($sub -> isAvailableAs('PrintBufferredDataGraphicsSubCmd') && $bufferedImg !== null) {
            // Append and flush buffer
            $classes = getBlockClasses($formatting);
            $classesStr = implode(" ", $classes);
            $outp[] = wrapInline("<div class=\"$classesStr\">", "</div>", imgAsDataUrl($bufferedImg));
            $lineHtml = "";
        }
    } else if ($cmd -> isAvailableAs('ImageContainer')) {
        // Append and flush buffer
        $classes = getBlockClasses($formatting);
        $classesStr = implode(" ", $classes);
        $outp[] = wrapInline("<div class=\"$classesStr\">", "</div>", imgAsDataUrl($cmd));
        $lineHtml = "";
        // Should load into print buffer and print next line break, but we print immediately, so need to skip the next line break.
        $skipLineBreak = true;
    }
    if ($cmd -> isAvailableAs('Code2DDataCmd')){
        $sub = $cmd -> subCommand();
        if ($debugMode)  {
            error_log("Subcommand ". get_class($sub) ."", 0); //Output the subcommand class in the debug console
            error_log("Function " . $sub->get_fn() ."",0);
            error_log("Data size:". $sub->getDataSize() ."",0);
            error_log("Data: '" . $sub->get_data() ."",0);
        }
        if($sub->isAvailableAs('QRcodeSubCommand')){ 
            switch ($sub->get_fn()) {
                case 65:  //set model
                    $code2dStorage->setQRModel($sub->get_data());
                    break;
                case 67: //set module size
                    $code2dStorage->setModuleSize($sub->get_data());
                    break;
                case 69: //select error correction level
                    $code2dStorage->setErrorCorrectLevel($sub->get_data());
                    break;
                case 80:  //Store QR data
                    $code2dStorage->fillSymbolStorage($sub->get_data());
                    break;
                case 81:  //Print the QR code
                    $qrcodeURI = $code2dStorage->getQRCodeURI();

                    if ($qrcodeURI == Code2DStatestorage::NO_DATA_ERROR){
                        error_log("QR code print ordered before contents stored.",0);
                        $imageData = base64_encode(file_get_contents('NoQR.JPG'));
                        $imgSrc = 'data: '.mime_content_type('NoQR.JPG').';base64,'.$imageData;
                        $qrcodeData = Code2dStatestorage::NO_DATA_ERROR;
                        $outp[] = "<img class=\"esc-bitimage\" src=\"$imgSrc\" alt=\"$qrcodeData\" />";
                    }
                    else {
                        $qrcodeData = $code2dStorage->getQRCodeData();
                        $outp[] = qrCodeAsDataUrl($qrcodeURI, $qrcodeData);
                    }
                    
                    break;
                case 82:  //Transmit size information of symbol storage data.
                    # TODO: maybe implement by printing the info?
                    break;
            }
        }
    }
}

// Stuff we need in the HTML header
const CSS_FILE = __DIR__ . "/src/resources/esc2html.css";
$metaInfo = array_merge(
    array(
        "<meta charset=\"UTF-8\">",
        "<style>"
    ),
    explode("\n", trim(file_get_contents(CSS_FILE))),
    array(
        "</style>"
    )
);

// Final document assembly
$receipt = wrapBlock("<div class=\"esc-receipt\">", "</div>", $outp);
$head = wrapBlock("<head>", "</head>", $metaInfo);
$body = wrapBlock("<body>", "</body>", $receipt);
$html = wrapBlock("<html>", "</html>", array_merge($head, $body), false);
echo "<!DOCTYPE html>\n" . implode("\n", $html) . "\n";
error_log("'". $targetFilename . "' converted to HTML",0);

function imgAsDataUrl($bufferedImg)
{
    $imgAlt = "Image " . $bufferedImg -> getWidth() . 'x' . $bufferedImg -> getHeight();
    $imgSrc = "data:image/png;base64," . base64_encode($bufferedImg -> asPng());
    $imgWidth = $bufferedImg -> getWidth() / 2; // scaling, images are quite high res and dwarf the text
    $bufferedImg = null;
    return "<img class=\"esc-bitimage\" src=\"$imgSrc\" alt=\"$imgAlt\" width=\"{$imgWidth}px\" />";
}

/* Creates the HTML image of a QR code
 Args:  
        bufferedQRImg: the Base64 encoded PNG image of the QR code
        qrcodeData: the data encoded in the QR code, to be put in the alt tag as an accessibility measure */
function qrCodeAsDataUrl($bufferedQRImg, $qrcodeData)
{
    $imgSrc = "data:image/png;base64," . $bufferedQRImg;
    return "<img class=\"esc-bitimage\" src=\"$imgSrc\" alt=\"$qrcodeData\" />";
}

function wrapInline($tag, $closeTag, $content)
{
    return $tag . $content . $closeTag;
}

function wrapBlock($tag, $closeTag, array $content, $indent = true)
{
    $ret = array();
    $ret[] = $tag;
    foreach ($content as $line) {
        $ret[] = ($indent ? '  ' : '') . $line;
    }
    $ret[] = $closeTag;
    return $ret;
}

function span(InlineFormatting $formatting, $spanContentText = false)
{
    // Gut some features-
    if ($formatting -> widthMultiple > 8) {
        // Widths > 2 are not implemented. Cap the width at 2 to avoid formatting issues.
        $formatting -> widthMultiple = 8;
    }
    if ($formatting -> heightMultiple > 8) {
        // Widths > 8 are not implemented either
        $formatting -> heightMultiple = 8;
    }

    // Determine formatting classes to use
    $classes = array();

    if ($formatting -> bold) {
        $classes[] = "esc-emphasis";
    }
    if ($formatting -> underline > 0) {
        $classes[] = $formatting -> underline > 1 ? "esc-underline-double" : "esc-underline";
    }
    if ($formatting -> invert) {
        $classes[] = "esc-invert";
    }
    if ($formatting -> upsideDown) {
        $classes[] = "esc-upside-down";
    }
    if ($formatting -> font == 1) {
        $classes[] = "esc-font-b";
    }
    if ($formatting -> widthMultiple > 1 || $formatting -> heightMultiple > 1) {
        $classes[] = "esc-text-scaled";
        // Add a single class representing height and width scaling
        $widthClass = $formatting -> widthMultiple > 1 ? "-width-" . $formatting -> widthMultiple : "";
        $heightClass = $formatting -> heightMultiple > 1 ? "-height-" . $formatting -> heightMultiple : "";
        $classes[] = "esc" . $widthClass . $heightClass;
    }

    // Provide span content as HTML
    if ($spanContentText === false) {
        $spanContentHtml = "&nbsp;";
    } else {
        $spanContentHtml = htmlentities($spanContentText);
    }

    // Output span with any non-default classes
    if (count($classes) == 0) {
        return $spanContentHtml;
    }
    return "<span class=\"". implode(" ", $classes) . "\">" . $spanContentHtml . "</span>";
}

function getBlockClasses($formatting)
{
    $classes = ["esc-line"];
    if ($formatting -> justification === InlineFormatting::JUSTIFY_CENTER) {
        $classes[] = "esc-justify-center";
    } else if ($formatting -> justification === InlineFormatting::JUSTIFY_RIGHT) {
        $classes[] = "esc-justify-right";
    }
    return $classes;
}
