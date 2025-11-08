<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\CommandOneArg;

class SelectBarCodeHriCmd extends CommandOneArg
{
    public function getHRI():?int{
        return $this->getArg();
    }
}
