<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\Code2DSubCommand;


class QRCodeSubCommand extends Code2DSubCommand
{

    private $fn = null;
    private $m = null;

    public function __construct($dataSize)
    {
        $this->dataSize = $dataSize;  //$dataSize is the size of fn+[parameters], so we exclude the fn byte
    }

    public function addChar($char)
    {
        if ($this->fn === null){
            //First extract the QR function
            $this -> fn = ord($char);
            $this->dataSize = $this->dataSize - 1; //subtract the size of fn from the size of the QR contents
            return true;
        }
        elseif ($this->fn == 80 && $this->m === null){
            //If this is the data storage function, extract the m value
            $this->m = ord($char);
            $this->dataSize = $this->dataSize - 1; //subtract the size of m from the size of the QR contents
            return true;
        } 
        else{ 
            //then send [parameters] into $data
            return parent::addChar($char);
        }
    }

    public function get_fn(){
        return $this->fn;
    }

    public function isAvailableAs($interface){
        return parent::isAvailableAs($interface);
    }
}