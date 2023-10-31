<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\DataSubCmd;

class Code2DSubCommand extends DataSubCmd
{

    public function getDataSize(){
        return $this->dataSize;
    }

    public function get_data(){
        return $this->data;
    }

}