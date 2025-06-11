<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\Command;
use ReceiptPrintHq\EscposTools\Parser\Command\TextContainer;
use ReceiptPrintHq\EscposTools\Parser\Context\InlineFormatting;
use ZBateson\MbWrapper\MbWrapper;

class TextCmd extends Command implements TextContainer
{
    private $str = "";

    public function addChar($char)
    {
        if (isset(Printout::$tree[$char])) {
            // Reject ESC/POS control chars.
            return false;
        }
        $this -> str .= $char;  //We don't convert the encoding on input anymore. See getText() below.
        return true;
    }


    /**
     * This function returns the UTF-8 encoded version of the text.
     * 
     * If no parameter is given, this assumes that the text is encoded as CP437 (aka Page 0)
     * 
     * This requires PHP 8.1.0+ to work.
     * @param InlineFormatting $context The current text formatting values, used to get the required encoding.
     */
    public function getText(InlineFormatting $context = new InlineFormatting)  
    {
        $text = "";

        $mbWrapper = new MbWrapper();

        $text = $mbWrapper->convert(str: $this -> str, fromCharset: $context -> charCodeTable, toCharset: "UTF-8");
        return $text;
    }
}
