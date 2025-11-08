<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\CommandOneArg;

class SetBarcodeWidthCmd extends CommandOneArg
{
    public function getWidth():?int{
        return $this->getArg();
    }
}
