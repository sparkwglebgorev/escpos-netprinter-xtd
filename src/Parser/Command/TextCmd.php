<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\Command;
use ReceiptPrintHq\EscposTools\Parser\Command\TextContainer;
use ReceiptPrintHq\EscposTools\Parser\Context\InlineFormatting;

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
     * This requires PHP 8.1.0+
     * @param InlineFormatting $context The current text formatting values, used to get the required encoding.
     */
    public function getText(InlineFormatting $context = new InlineFormatting)  
    {
        $text = "";

        if ($context -> charCodeTable = "CP437"){
            $text = iconv(from_encoding: "CP437", to_encoding: "UTF-8", string: $this -> str);
        }
        else {
            $text = mb_convert_encoding(string: $this -> str, to_encoding: "UTF-8", from_encoding: $context -> charCodeTable);
        }
        return $text;
    }
}
