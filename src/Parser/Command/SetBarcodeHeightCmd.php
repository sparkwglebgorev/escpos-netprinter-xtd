<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\CommandOneArg;

class SetBarcodeHeightCmd extends CommandOneArg
{
    public function getHeight(): ?int{
        return $this->getArg();
    }
}
